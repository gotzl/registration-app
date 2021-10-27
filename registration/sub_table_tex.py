#!/usr/bin/env python3
import shutil, re
from io import StringIO
import os
import string
import subprocess
from django.utils.translation import gettext_lazy as _, ngettext_lazy


LATEX_TEMPLATE = string.Template(
    r'''\documentclass[a4paper]{article}
\usepackage[ngerman]{babel}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}

$options
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{pifont}
\usepackage[%
    left=0.50in,%
    right=0.50in,%
    top=1.0in,%
    bottom=1.0in,%
    paperheight=11in,%
    paperwidth=8.5in%
]{geometry}%

\title{$title}
	 
\begin{document}
\maketitle

\begin{center}
\begin{longtable}{ r p{0.15\textwidth} p{0.15\textwidth} p{0.35\textwidth} | r | c | c}
$header
\toprule
$rows
\end{longtable}
\end{center}
\end{document} 
    '''
)


# https://stackoverflow.com/questions/16259923/how-can-i-escape-latex-special-characters-inside-django-templates
def tex_escape(text):
    """
        :param text: a plain text message
        :return: the message escaped to appear correctly in LaTeX
    """
    conv = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\^{}',
        '\\': r'\textbackslash{}',
        '<': r'\textless{}',
        '>': r'\textgreater{}',
    }
    regex = re.compile('|'.join(re.escape(str(key)) for key in sorted(conv.keys(), key = lambda item: - len(item))))
    return regex.sub(lambda match: conv[match.group()], text)


def create_table(subjects):
    project_path = os.path.curdir
    build_path = os.path.join(project_path, '.build')
    out_filename = os.path.join(build_path, 'template')
    documentclass_name = 'article'

    options = []
    options_latex = '\n'.join(
        r'\newcommand{\%s}{%s}' % pair for pair in options
    )
    options_latex = ''
    title = ''

    if len(subjects)>0:
        title = str(subjects[0].event)
        seats = subjects[0].event.num_max_per_subject

    rows = StringIO()
    for i, sub in enumerate(subjects):
        row =  list(map(tex_escape, [
            str(i+1),
            sub.name,
            sub.given_name,
            sub.email]))
        row.extend([
            sub.seats,
            '\\ding{51}' if sub.status_confirmed else '\\ding{55}',
            ''
        ])
        rows.write('%s\\\\ \\hline \n' % ' & '.join(row))

    header = '%s\\\\ \n' % ' & '.join(
        map(str, ['', _('name'), _('given_name'), _('email'), 
            ngettext_lazy('seat','seats', seats), _('confirmed'), _('present')]))

    latex = LATEX_TEMPLATE.safe_substitute(
        options=options_latex, documentclass=documentclass_name,
        title=title,
        header=header, rows=rows.getvalue(),
    )

    shutil.rmtree(build_path, ignore_errors=True)

    os.makedirs(build_path, exist_ok=True)
    with open(out_filename + '.tex', 'w') as out_file:
        out_file.write(latex)

    subprocess.run(['pdflatex', '-output-directory', build_path, out_filename])
    # shutil.copy2(out_filename + '.pdf', os.path.dirname(in_filename))
    return out_filename+'.pdf'
