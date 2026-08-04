---
name: traffic-law-docs
description: parse traffic accident legal documents and generate exam answers. use when user needs to extract text from word documents in e jiaotong directory, parse traffic safety exam papers, or generate structured legal knowledge base. supports batch processing of legal documents, exam paper analysis, and answer generation based on traffic laws.
---

# traffic law documents parser

parse traffic accident legal documents and generate exam answers based on chinese traffic safety laws.

## overview

this skill provides tools for:
1. batch parsing legal documents - extract text from doc and docx files
2. building legal knowledge base - generate structured json from parsed documents
3. exam paper processing - parse exam papers and generate complete answers
4. legal citation - reference specific articles from traffic laws

## when to use

use this skill when:
- user asks to parse documents in e jiaotong directory
- user needs to extract text from word documents
- user wants to generate exam answers for traffic safety exams
- user needs to query specific traffic law articles
- user asks about traffic accident legal provisions

## supported document types

| document type | extension | parser |
|--------------|-----------|--------|
| word document old | doc | word com |
| word document new | docx | word com |
| legal regulations | doc docx | word com |
| exam papers | docx | word com |

## core workflow

### 1. parse legal documents

initialize word com to parse documents and extract text content.

### 2. batch process directory

process all doc and docx files in the legal documents directory.

### 3. generate exam answers

parse exam paper content, identify question types, and generate answers based on traffic laws.

## output format

### legal knowledge base json

```json
{
  "filename": {
    "filename": "original filename",
    "path": "full path",
    "content": "document content",
    "articles": {
      "article1": "content"
    }
  }
}
```

### exam answer document

markdown format with question number, correct answer, legal basis, and explanation.

## key legal references

### primary laws
- chinese traffic safety law
- chinese traffic safety law implementation regulations
- chinese civil code tort liability

### judicial interpretations
- supreme court interpretation on traffic accident compensation
- supreme court interpretation on personal injury compensation

### regulations
- traffic accident handling procedures
- compulsory traffic accident liability insurance regulations

### standards
- human body injury disability grading
- labor capacity assessment standards

## common tasks

### task parse all legal documents

1. check if e jiaotong laws directory exists
2. get all doc and docx files
3. parse each document
4. build json structure
5. save to traffic laws parsed json

### task generate exam answers

1. parse exam paper
2. identify question types
3. generate answers with legal references
4. create markdown answer document

### task query specific article

1. load parsed json
2. search for article number
3. return article content

## important notes

- save output as utf-8 for chinese characters
- requires microsoft word installed
- release com objects after use
- some old doc files may fail to parse

## example usage

user asks to parse legal documents
action batch parse all files and generate json

user asks to fill exam answers
action parse exam and generate answers

user asks about law article 76
action query json and return article content

## file locations

- source documents e jiaotong laws
- parsed output traffic laws parsed json
- exam answers exam answers md
