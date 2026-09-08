#!/usr/bin/env python3

import re
import sys
from collections import Counter
import glob


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

# Tokens reconnus :
#
#   (\^1#
#   [\^1#
#   [\^
#   (\^
#   [
#   (
#   {CB1.
#   {=DIAG.
#   {LAT.
#   }
#   ]
#   )
#
# Regex :
#
# (\(\^\d#)|(\[\^\d#)|(\[\^)|(\(\^)|(\[)|(\()|\{([=]?[A-Za-z0-9_]+[=]?)\.?|[}\])]
#
TOKEN_RE = re.compile(
    r'(\(\^\d#)|(\[\^\d#)|(\[\^)|(\(\^)|(\[)|(\()|\{([=]?[A-Za-z0-9_]+[=]?)\.?|[}\])]'
)


# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------

def validate_file(filename):

    stack = []

    errors = []
    stats = Counter()

    with open(filename, "r", encoding="utf-8") as f:

        for line_no, line in enumerate(f, start=1):

            # ------------------------------------------------
            # Recherche de tous les tokens dans l'ordre
            # ------------------------------------------------

            for match in TOKEN_RE.finditer(line):

                token = match.group(0)
                column = match.start() + 1

                # ====================================================
                # OUVERTURES
                # ====================================================

                # ------------------------------------------------
                # Ouvertures de type parenthèse
                #
                # (
                # (^
                # (^1#
                # ------------------------------------------------

                if (
                    token == "("
                    or token == "(^"
                    or re.fullmatch(r'\(\^\d#', token)
                ):

                    stack.append({
                        "type": "parenthesis",
                        "token": token,
                        "line": line_no,
                        "column": column,
                    })

                    stats["open"] += 1
                    stats["open_parenthesis"] += 1

                # ------------------------------------------------
                # Ouvertures de type crochet
                #
                # [
                # [^
                # [^1#
                # ------------------------------------------------

                elif (
                    token == "["
                    or token == "[^"
                    or re.fullmatch(r'\[\^\d#', token)
                ):

                    stack.append({
                        "type": "bracket",
                        "token": token,
                        "line": line_no,
                        "column": column,
                    })

                    stats["open"] += 1
                    stats["open_bracket"] += 1

                # ------------------------------------------------
                # Ouverture de type accolade
                #
                # {CB1.
                # {=DIAG.
                # {LAT.
                # ------------------------------------------------

                elif token.startswith("{"):

                    # Retirer le {
                    tag = token[1:]

                    # Retirer le point final s'il existe
                    if tag.endswith("."):
                        tag = tag[:-1]

                    tag = tag.strip()

                    if not tag:

                        errors.append(
                            f"ligne {line_no}, colonne {column}: "
                            f"balise vide"
                        )

                        stats["empty_tag"] += 1
                        continue

                    stack.append({
                        "type": "brace",
                        "tag": tag,
                        "token": token,
                        "line": line_no,
                        "column": column,
                    })

                    stats["open"] += 1
                    stats["open_brace"] += 1

                # ====================================================
                # FERMETURES
                # ====================================================

                elif token in ("}", "]", ")"):

                    stats["close"] += 1

                    # ------------------------------------------------
                    # Aucun élément ouvert
                    # ------------------------------------------------

                    if not stack:

                        errors.append(
                            f"ligne {line_no}, colonne {column}: "
                            f"'{token}' orphelin"
                        )

                        stats["orphan_close"] += 1
                        continue

                    opened = stack[-1]

                    # ------------------------------------------------
                    # Déterminer le type attendu
                    # ------------------------------------------------

                    if token == "}":
                        expected_type = "brace"
                        expected_close = "}"

                    elif token == "]":
                        expected_type = "bracket"
                        expected_close = "]"

                    else:
                        expected_type = "parenthesis"
                        expected_close = ")"

                    # ------------------------------------------------
                    # Mauvais type de fermeture
                    # ------------------------------------------------

                    if opened["type"] != expected_type:

                        if opened["type"] == "brace":
                            expected = "}"

                        elif opened["type"] == "bracket":
                            expected = "]"

                        else:
                            expected = ")"

                        errors.append(
                            f"ligne {line_no}, colonne {column}: "
                            f"fermeture '{token}' incorrecte, "
                            f"fermeture '{expected}' attendue pour "
                            f"'{opened['token']}' ouvert ligne "
                            f"{opened['line']}, colonne "
                            f"{opened['column']}"
                        )

                        stats["mismatched_close"] += 1

                        # On ne dépile PAS :
                        # l'ouverture est toujours active.
                        continue

                    # ------------------------------------------------
                    # Fermeture correcte
                    # ------------------------------------------------

                    stack.pop()

                    stats["matched"] += 1

                # ====================================================
                # Token inconnu
                # ====================================================

                else:

                    errors.append(
                        f"ligne {line_no}, colonne {column}: "
                        f"token inattendu '{token}'"
                    )

                    stats["unexpected"] += 1

    # ============================================================
    # Balises encore ouvertes à la fin du fichier
    # ============================================================

    if stack:

        for item in reversed(stack):

            errors.append(
                f"ligne {item['line']}, colonne {item['column']}: "
                f"balise non fermée : {item['token']}"
            )

        stats["unclosed"] += len(stack)

    # ============================================================
    # Rapport
    # ============================================================

    print()
    print("=" * 70)
    print("RAPPORT DE VALIDATION")
    print("=" * 70)
    print()

    print(f"Fichier : {filename}")
    print()

    print("Statistiques")
    print("-" * 70)

    print(f"Ouvertures détectées     : {stats['open']}")
    print(f"  dont '{{'              : {stats['open_brace']}")
    print(f"  dont '['              : {stats['open_bracket']}")
    print(f"  dont '('              : {stats['open_parenthesis']}")
    print(f"Fermetures détectées     : {stats['close']}")
    print(f"Paires correspondantes   : {stats['matched']}")
    print(f"Fermetures orphelines    : {stats['orphan_close']}")
    print(f"Fermetures incorrectes   : {stats['mismatched_close']}")
    print(f"Balises non fermées      : {stats['unclosed']}")
    print()

    if errors:

        print("=" * 70)
        print(f"PROBLÈMES ({len(errors)})")
        print("=" * 70)

        for error in errors:
            print(error)

        print()

        return False

    print("=" * 70)
    print("OK : aucune anomalie détectée")
    print("=" * 70)

    return True


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

if __name__ == "__main__":

    if len(sys.argv) < 2:

        print(
            f"Usage : {sys.argv[0]} 'fichier(s)'",
            file=sys.stderr
        )

        sys.exit(2)

    filenames = glob.glob(sys.argv[1])

    print(filenames)

    if not filenames:

        print(
            f"Aucun fichier trouvé pour : {sys.argv[1]}",
            file=sys.stderr
        )

        sys.exit(2)

    for file in filenames:

        try:

            valid = validate_file(file)

        except UnicodeDecodeError as e:

            print(
                f"Erreur d'encodage : {e}",
                file=sys.stderr
            )

            sys.exit(2)

        except FileNotFoundError:

            print(
                f"Fichier introuvable : {file}",
                file=sys.stderr
            )

            sys.exit(2)

        if valid:

            print("C valide")

        else:

            sys.exit(1)