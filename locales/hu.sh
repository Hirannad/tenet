# hu — Hungarian section names.
#
# Sourced by skills/tenet/scripts/lib.sh when the vault's _meta/locale says `hu`
# (or TENET_LOCALE=hu is set for one run). It overrides the English defaults and
# nothing else: the scripts, the reports and the reference docs stay English.
#
# This is the worked example for writing another one. A locale is six strings —
# if yours needs more than that, the thing you are localising is not the section
# names, and it belongs in a fork rather than here.
#
# The headings must match the vault's notes EXACTLY, including case and accents.
# SECTION_DECISION is the one the 60-word cap matches on, so a mismatch there
# silently reports every note as having no decision section at all.
#
# WHAT A LOCALE DOES NOT DO: it does not translate vault-template/templates/.
# bootstrap.sh copies those verbatim, and nothing here reaches them — so choosing
# a locale means translating the templates in your own vault by hand, once. Until
# you do, notes written from an English template carry English headings while the
# checks look for these, which is the silent zero warned about two lines up. The
# six strings cover the decision template only; the other four templates have
# fifteen headings between them and no locale string at all. Translate the
# headings INSIDE the files and leave the filenames as `* Template.md` — every
# saved view excludes templates by filename.

SECTION_DECISION="Döntés"
SECTION_REVISIT="Mikor kell újragondolni"
SECTION_WHY="Miért"
SECTION_BACKGROUND="Előzmény"
SECTION_OPTIONS="Mérlegelt opciók"
SECTION_DILEMMA="A dilemma"
