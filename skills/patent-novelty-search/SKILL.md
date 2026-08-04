# Patent Novelty Search Skill

---
name: novelty-search
description: Execute the patent novelty search process, including technical solution analysis, patent retrieval, feature comparison, and novelty search report generation. This skill is used when users need to conduct patent novelty search, novelty analysis of technical solutions, retrieve related patents, and generate novelty search reports. It supports the complete process: input structured processing, technical feature extraction, patent retrieval (prioritizing Google Patents), similarity ranking, feature comparison table generation, novelty/inventive step comment, and finally output a novelty search report in Word format.
---

# Patent Novelty Search Skill

Execute the complete patent novelty search process, from user input to generating a professional novelty search report.

## When to Use

When users:
- Mention "patent novelty search", "novelty search report", "novelty retrieval"
- Need to analyze patent risks of technical solutions
- Request to retrieve related patents and conduct comparative analysis
- Require generating patent novelty search documents
- Input technical solution descriptions and request evaluation of novelty or inventive step

## Workflow

### Step 1: User Input Structured Processing

**Objective**: Extract the core three elements from user input.

**Processing Requirements**:
1. **Technical Problem**: Identify the technical problem to be solved by the user's solution.
2. **Technical Means**: Extract specific technical means for implementing the technical solution.
3. **Technical Effect**: Analyze the technical effects brought by the technical solution.

**Notes**:
- Delete invalid, duplicate, and incorrect information.
- Retain all valuable technical information.
- Make reasonable inferences and supplements for vague descriptions.
- Output a structured three-element table.

**Output Format**:
```
【Technical Problem】
Example: Tea contains a strong bitter and astringent taste that affects the taste, especially the presence of bitter components such as bitter amino acids and theophylline, leading to poor taste of tea soup.
...
【Technical Means】
Example: A tea processing technology includes the following steps: screening newly picked tea leaves with a sieve to select tea leaves with uniform size and remove pedicels; stir-frying green in an iron wok; inhibiting and inactivating enzyme activity in fresh leaves through the iron wok and heat control; manual twisting forward and backward 108 times; separating tea pedicels through three sieving processes; spreading the twisted tea leaves thinly; spreading the tea leaves thinly and naturally air-drying until the water loss rate is about 80%-85%, then re-polymerizing and transforming; releasing gas every Chen hour to expel the accumulated gas of the night and reintroduce fresh air to fully activate the tea's qi; undergoing natural fermentation of seven releases and seven accumulations to stabilize the tea qi after storage in a warehouse for 28 days; pressing the finished tea into cakes with mineral water with multiple minerals (special water treatment). Among them, the screened tea leaves are spread and air-dried at a place 1 meter above the ground on a well-ventilated tea sieve or tea mat to prevent secondary oxidation caused by ground heat entering the tea leaves; the stir-fried tea leaves are spread and air-dried for 3-6 days to make the water loss rate of the tea leaves about 35%-40%; drying with two sieves until the water content of the tea leaves is about 10% of the new leaves.
...
【Technical Effect】
Example: Through an orderly processing step, this technology fully reacts with bitter components in tea such as bitter amino acids and theophylline, thereby decomposing the bitter taste in tea and reducing the bitter and astringent taste to ensure the taste. Meanwhile, this technology retains various aromatic flavors of tea in nature and enhances the taste of brewed tea.
...
```
Note: Each of the three elements is a single paragraph and should not be split.

### Step 2: Extract Technical Features

**Objective**: Disassemble technical means and extract technical features, which must be completely derived from the technical means.

**Extraction Principles**:
1. **The first technical feature must be the technical subject** (e.g., a certain XX device, a certain XX method).
2. The granularity of splitting should be reasonable:
   - Too coarse: The technical feature is too long, making subsequent comparison difficult.
   - Too fine: It will split technical information and lead to inaccurate subsequent comparison.
3. Each feature should be independent, complete, and comparable.
4. Sort in the order of appearance in the technical means.

**Output Format**:
```
【Technical Feature List】
1. Technical Subject: [Technical subject description]
2. Technical Feature 2: [Feature description]
3. Technical Feature 3: [Feature description]
...
```

### Step 3: Patent Retrieval

**Objective**: Retrieve related patents based on the three elements.

**Retrieval Strategy**:

**Prioritize using the Google Patents website** (patents.google.com):
1. Use the `browser_use` tool to open Google Patents.
2. Construct retrieval formulas:
   - Keyword combination: Technical problem + technical means + technical effect
   - IPC classification number (if determinable)
   - Synonym expansion
3. Execute retrieval and collect results.

**If Google Patents is inaccessible**:
- Use other patent databases (e.g., Chinese Patent Publication Announcement Network, Espacenet, WIPO, etc.)
- Or retrieve patent information through search engines.

**Retrieval Requirements**:
- Retrieve at least 50 related patents (Note: Ensure the patent data is from actual retrieval).
- Record basic information of each patent:
  - Patent/publication number
  - Title
  - Applicant/patentee
  - Publication date
  - Abstract
  - IPC classification number

**Output Retrieval Strategy Table**
```
No. | Retrieval Step | Retrieval Strategy | Retrieval Results
1 | Semantic Retrieval | Semantic text | 5034
2 | Boolean Retrieval | Retrieval formula | 21
...
```

### Step 4: Similarity Ranking

**Objective**: Evaluate and rank the retrieval results by similarity.

**Evaluation Dimensions**:
1. Technical field similarity
2. Technical problem similarity to be solved
3. Technical means similarity
4. Technical effect similarity

**Ranking Method**:
- Conduct a comprehensive score (0-100 points) for each patent.
- Sort from high to low by score.
- Output the top 50 patent list.

**Output Format**:
```
No. | Similarity | Patent No. | Title | Applicant | Publication Date | IPC
----|--------|--------|------|--------|----------|-----
1 | ⭐⭐⭐ | CNxxx | xxx | xxx | 2024-01-01 | H01L
2 | ⭐⭐ | USxxx | xxx | xxx | 2023-06-15 | G06F
...
```
Similarity is displayed with 0-5 stars; the more stars, the higher the similarity.

### Step 5: Feature Comparison Analysis

**Objective**: Conduct a detailed comparison of the top 3 patents with the highest similarity.

**Extract Related Content of Prior Art Documents**:
For each technical feature, extract the content related to the feature from the prior art documents, and display the comparison result label under the related content in the feature comparison table.

**Comparison Result Labels**:
1. **Disclosed**: The prior art document clearly records the technical feature.
2. **Common General Knowledge**: The prior art document does not record it, but it belongs to common general knowledge in the field.
3. **Not Disclosed**: The prior art document does not record it, and it is not common general knowledge.

**Comparison Table Format**:

| Technical Feature | Prior Art Document 1 (Patent No.) | Prior Art Document 2 (Patent No.) | Prior Art Document 3 (Patent No.) |
|---------|-------------------|-------------------|-------------------|
| Feature 1 (Technical Subject) | Related content / Disclosed / Common General Knowledge / Not Disclosed | Related content / Disclosed / Common General Knowledge / Not Disclosed | Related content / Disclosed / Common General Knowledge / Not Disclosed |
| Feature 2 | Related content / Disclosed / Common General Knowledge / Not Disclosed | Related content / Disclosed / Common General Knowledge / Not Disclosed | Related content / Disclosed / Common General Knowledge / Not Disclosed |
| ... | ... | ... | ... |

**Comparison Requirements**:
- Each judgment must be based on the specific content of the prior art document, strictly from the prior art.
- Judgments of "Common General Knowledge" must state the reasons (standards, textbooks, conventional technologies, etc.).
- The comparison should be objective and accurate.

### Step 6: Novelty/Inventive Step Comment

**Objective**: Determine the patent type and write comments based on the comparison results.

**Comment Types**:

**X Document (Novelty Comment)**:
- A single prior art document discloses all technical features.
- Comment Points: Explain which technical features are disclosed by the prior art document, and draw the conclusion that the user's solution lacks novelty.

**X Document (Inventive Step Comment)**:
- A single prior art document discloses part of the technical features.
- The remaining technical features belong to common general knowledge.
- Comment Points: Explain the disclosed part and common general knowledge part, and draw the conclusion that the user's solution lacks inventive step.

**Y Document (Inventive Step Comment)**:
- Multiple patents need to be combined to disclose or know all technical features.
- Comment Points: Explain what is disclosed by Prior Art Document 1, what are the distinguishing technical features, what is disclosed by other prior art documents, and how to combine and the motivation for combination, and draw the conclusion that the user's solution lacks inventive step.

**Comment Format**:
```
【Prior Art Document X】Patent No.: xxx, Title: xxx

Comparative Analysis:
- Disclosed Technical Features: [List]
- Common General Knowledge Technical Features: [List]
- Undisclosed Technical Features: [List]

Conclusion: [X Document/Y Document] - [Novelty Comment/Inventive Step Comment]

Detailed Comment:
[Detailed comment content]
```

### Step 7: Generate Novelty Search Report

**Objective**: Output a complete novelty search report (Word format).

**Report Structure**:

```
Patent Novelty Search Report

I. User Solution
   1. Technical Problem
   2. Technical Means
   3. Technical Effect

II. Technical Features
   [Technical Feature List]

III. Feature Comparison Table
   [Comparison Table]

IV. Novelty/Inventive Step Comment (If it is an X document, comment on a single document; if it is a Y document, comment on the combination of multiple documents)
   [Novelty Comment]
   [Inventive Step Comment]

V. Novelty Search Conclusion
   [Comprehensive Conclusion]

VI. Retrieval Strategy
   [Retrieval Strategy Table]

VII. Related Patent List
   [50 Patent List]
```
**Disclaimer (Must be indicated on the first page of the report)**
Refer to 'references/disclaimer.md.'

**Use docx skill to generate the report**:
1. Call the docx skill to create a Word document with professional formatting.
2. Include a cover page, table of contents, and main text.
3. Standardize table formatting.
4. Save as a `.docx` file and provide it to the user.

## Tool Usage

### Browser Retrieval
```
Use the browser_use tool:
1. Open the Google Patents website: action=open, url=https://patents.google.com
2. Input retrieval formula: Enter the keyword combination in the search box.
3. Obtain results: Use snapshot to get page content.
4. Turn pages to obtain more results.
```

### Document Generation
```
Use the docx skill:
1. Create the document structure.
2. Fill in content for each chapter.
3. Insert tables and formatting.
4. Save and provide the document to the user.
```

## Notes

1. **Objectivity**: All judgments must be based on evidence and avoid subjective assumptions.
2. **Accuracy**: Patent information must be accurate and error-free.
3. **Completeness**: The report must contain all necessary content.
4. **Professionalism**: Use standardized patent terminology.
5. **Timeliness**: Pay attention to the legal status of patents.

## Error Handling

- If Google Patents is inaccessible, automatically switch to other patent databases.
- If the retrieval results are less than 50, state the reason and continue the analysis.
- If there are disputes in feature comparison, record them truthfully and explain.
- If common general knowledge cannot be determined, mark that further verification is required.

## Quality Control
After completing each step:
When starting execution, confirm the following checklist internally:
Step 1: Generated three elements (technical problem/means/effect)
Step 2: Extracted technical features (F1 is the technical subject, a total of N features)
Step 3: Completed actual patent retrieval using web_search/web_fetch
Step 4: Generated a sorted patent list (at least 10, preferably 50)
Step 5: Generated a feature comparison table for D1/D2/D3 respectively (three dimensions: Disclosed/Common General Knowledge/Not Disclosed)
Step 6: Generated novelty/inventive step comments based on the comparison results
Step 7: Read the docx skill, generated a .docx report, and provided it to the user through present_files

## Reference Documents
- references/search-strategies.md: Retrieval strategies and keyword templates for common technical fields