# 案件简报的 LaTeX 前言

## article 前言

```latex
\documentclass[12pt]{article}
\usepackage[utf8]{inputenc}
\usepackage{setspace}
\setlength{\parindent}{2em}
\setlength{\parskip}{1.25em}
\renewcommand{\baselinestretch}{1.0}
\usepackage{titling}
\newcommand{\subtitle}[1]{%
  \posttitle{%
    \par\end{center}
    \begin{center}\large#1\end{center}
    \vskip0.5em}%
}

\title{[Case Name]}
\subtitle{Case Brief}
\author{}
\date{}

\begin{document}
\maketitle
```

## Beamer 演示前言

```latex
\documentclass{beamer}
\usetheme{Madrid} % Modern theme with gradient headers
\usecolortheme{seahorse} % Professional blue-gray tones
\setbeamertemplate{itemize items}[circle] % Clean circular bullet points
\usepackage{graphicx} % For icons
\usepackage{xcolor}

% Custom colors
\definecolor{lawblue}{RGB}{0,51,102}
\definecolor{lawgold}{RGB}{204,153,0}
\setbeamercolor{title}{fg=lawblue}
\setbeamercolor{frametitle}{fg=lawblue}
\setbeamercolor{itemize item}{fg=lawgold}

\usepackage{booktabs}

\title{[Case Name]}
\subtitle{Case Brief}
\author{}
\date{}

\begin{document}
\frame{\titlepage}
```

## Beamer 幻灯片指南

- 每张幻灯片目标约 5 个主要项目
- 每个项目最多 2 个子项目
- 每张幻灯片项目和子项目总数最多 9 个
- 对必须保持在一起的长内容使用 `\begin{frame}[allowframebreaks]`

### 示例幻灯片结构

```latex
\begin{frame}{Section Title}
\begin{itemize}
    \item First main point
        \begin{itemize}
            \item Supporting detail
        \end{itemize}
    \item Second main point
    \item Third main point
        \begin{itemize}
            \item Supporting detail A
            \item Supporting detail B
        \end{itemize}
    \item Fourth main point
    \item Fifth main point
\end{itemize}
\end{frame}
```

## 章节简报格式（无前言）

对打算纳入更大案例教科书项目的章节简报，**不要**包含任何前言。直接以：

```latex
\chapter{Case Name, Citation}

\section{Detailed Case Facts}
...
```

开始。父文档将处理所有格式和宏包导入。
