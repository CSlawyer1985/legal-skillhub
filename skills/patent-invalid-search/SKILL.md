# Patent Invalidation
## Description
Execute the patent invalidation analysis process, including input verification (independent solution and filing date), extraction of technical features, targeted evidence search, feature comparison, and commentary on invalidity grounds (evidence combination). Support the entire process from input review to generating a Word-format invalidation analysis report.

# Patent Invalidation Skills
Evaluate the validity of a target patent through in-depth retrieval of prior art, and construct invalidity grounds and evidence chains.

## When to Use
When the user:
* Mentions "patent invalidation", "challenging patent rights", or "patent validity stability analysis"
* Needs to find the "Prior Art" of a specific patent
* Requests a comparison of the technical features of a patent to destroy its novelty or inventiveness
* Needs to generate a professional patent invalidation analysis report

## Workflow
### Step 1: User Input Verification and Judgment (Key Pre-Check)
**Objective**: Ensure the analysis object is clear and has a time benchmark.

**Execution Logic**:
1. **Filing Date/Priority Date Check**: Verify if the user has provided the filing date (or priority date) of the target patent.
    * **If not**: Prompt the user to provide it and state: "To accurately screen prior art, please provide the filing date or priority date of the target patent."
2. **Independence Check of Technical Solution**: Determine if the input content is a specific and complete technical solution.
    * **If incomplete**: Prompt the user to supplement it.
    * **If the description is chaotic/contains multiple technical solutions**: The AI attempts to summarize an "independent technical solution" and ask the user: "Your input contains multiple technical solutions, which I have summarized into one. Please confirm whether to proceed with the analysis?"

### Step 2: Structured Processing of Technical Solutions
**Objective**: Extract the core targets for invalidation attacks.

**Processing Requirements**:
1. **Technical Problem**: The problem claimed to be solved by the target patent.
2. **Technical Means**: A combination of specific technical features for implementing the solution.
3. **Technical Effect**: The effect claimed to be achieved by the target patent.

**Notes**:
- Delete invalid, repetitive, and incorrect information
- Retain all valuable technical information
- Make reasonable inferences and supplements for ambiguous descriptions
- Output a structured three-element table

**Output Format**:
```
【Technical Problem】
Example: Tea contains a strong bitter and astringent taste that affects the mouthfeel. The presence of bitter components such as bitter amino acids and theophylline leads to an unpleasant taste of tea soup.
...
【Technical Means】
Example: A tea processing technology includes the following steps: screening newly picked tea leaves with a sieve to remove pedicels from tea leaves of uniform size; stir-frying in an iron wok; inhibiting and inactivating enzyme activity in fresh leaves through the iron wok and heat control; twisting manually 108 times clockwise and counterclockwise; separating tea pedicels through three rounds of beating; spreading the twisted tea leaves thinly; spreading the tea leaves thinly and performing natural air-drying until the water loss rate is about 80%-85%, then re-polymerizing and transforming; releasing gas at the Chen hour every day to expel accumulated gas from the night and reintroduce fresh air, fully activating the tea's qi; undergoing natural fermentation through seven cycles of releasing and retaining qi, followed by 28 days of warehouse storage to stabilize the tea's qi; pressing the finished tea into cakes with mineral-rich water from a special spring. Among them, the screened tea leaves are spread and air-dried at a height of one meter above the ground on a well-ventilated tea sieve or mat to prevent secondary oxidation caused by ground heat; the stir-fried tea leaves are spread and air-dried for 3-6 days to reduce the water content to about 10% of the fresh leaves.
...
【Technical Effect】
Example: This process fully reacts with bitter components such as bitter amino acids and theophylline in tea through ordered processing steps, thereby decomposing the bitter taste in tea and reducing its astringency to ensure a good mouthfeel. Meanwhile, this process retains various aromatic flavors of tea in nature and enhances the taste of brewed tea.
...
```
Note: Each of the three elements is a single paragraph and should not be split.

### Step 3: Extraction of Technical Features
**Objective**: Disassemble technical means to extract technical features, which must be entirely derived from the technical means.

**Extraction Principles**:
1. The first technical feature must be the technical subject matter (e.g., "A XX device", "A XX method").
2. The granularity of splitting should be reasonable:
   - Too coarse: The technical feature is too long, making subsequent comparison difficult.
   - Too fine: It will割裂 technical information and lead to inaccurate subsequent comparison.
3. Each feature should be independent, complete, and comparable.
4. Sort in the order of appearance in the technical means.

**Output Format**:
```
【List of Technical Features】
1. Technical Subject Matter: [Description of Technical Subject Matter]
2. Technical Feature 2: [Description of Feature]
3. Technical Feature 3: [Description of Feature]
...
```

### Step 4: Patent Search (Finding Evidence Documents)
**Objective**: Search for prior art (Evidence) published **before the filing date**.

**Search Strategy**:
**Priority: Use the Google Patents website (patents.google.com)**:
1. Use the `browser_use` tool to open Google Patents.
2. Construct search queries:
   - Keyword combination: Technical Problem + Technical Means + Technical Effect
   - IPC classification number (if determinable)
   - Synonym expansion
3. Execute the search and collect results.

**If Google Patents is inaccessible**:
- Use other patent databases (e.g., Chinese Patent Publication and Announcement Network, Espacenet, WIPO, etc.)
- Or search for patent information via search engines.

**Search Requirements**:
- Retrieve at least 50 relevant patents (Note: Ensure the patent data is real and the publication date is before the input filing date/priority date of the target patent).
- Record basic information of each patent:
  - Patent No./Publication No.
  - Title
  - Applicant/Patentee
  - Publication Date
  - Abstract
  - IPC Classification Number

**Output Search Strategy Table**:
```
No. | Search Step | Search Strategy | Search Results
1 | Semantic Search | Semantic Text | 5034
2 | Boolean Search | Search Query | 21
...
```

### Step 5: Similarity Ranking (Evidence Evaluation)
**Objective**: Evaluate and sort the search results by similarity.

**Evaluation Dimensions**:
1. Similarity in technical field
2. Similarity in technical problems solved
3. Similarity in technical means
4. Similarity in technical effects

**Ranking Method**:
- Assign a comprehensive score (0-100 points) to each patent.
- Sort from highest to lowest score.
- Output a list of the top 50 patents.

**Output Format**:
```
No. | Similarity | Patent No. | Title | Applicant | Publication Date | IPC
----|------------|------------|-------|-----------|------------------|-----
1 | ⭐⭐⭐⭐⭐ | CNxxx | xxx | xxx | 2024-01-01 | H01L
2 | ⭐⭐⭐⭐ | USxxx | xxx | xxx | 2023-06-15 | G06F
...
```
Similarity is displayed with 0-5 stars; the more stars, the higher the similarity.

### Step 6: Feature Comparison and Analysis
**Objective**: Compare the strongest evidence (E1, E2, E3) one by one with the technical features of the target patent.

**Comparison Result Labels**:
1. **Disclosed**: Clearly recorded in the evidence.
2. **Common General Knowledge/Easily Obtained**: Not recorded in the evidence but belonging to common means in the field.
3. **Not Found**: Not found in the current evidence.

| Technical Feature | Evidence 1 (E1) | Evidence 2 (E2) | Evidence 3 (E3) |
|-------------------|-----------------|-----------------|-----------------|
| Feature 1 | Content + Label | Content + Label | Content + Label |

### Step 7: Invalidation Commentary and Conclusion
**Objective**: Construct legal logic to determine whether the patent right can be overturned.

**Commentary Types**:
1. **Novelty Destruction (Separate Comparison)**: E1 completely covers all technical features.
2. **Inventiveness Destruction (Combined Comparison)**:
   * E1 + Common General Knowledge.
   * E1 + E2 (+E3): Explain that E1 is the closest prior art, and E2 provides technical inspiration for the remaining features, with motivation for their combination.

**Output Format**:
```
【Analysis of Invalidation Grounds】
- Evidence Combination: E1 + E2
- Legal Basis: Article 22, Paragraph 3 of the Patent Law (Inventiveness)
- Commentary Logic: [Detailed explanation of the combination path and motivation]
- Conclusion: The validity of Claim X of the target patent is low, with a high probability of being invalidated.
```

### Step 8: Generate Invalidation Analysis Report (Word)
**Report Structure**:
```
Patent Invalidation Report

1. User's Solution
   1.1 Technical Problem
   1.2 Technical Means
   1.3 Technical Effect

2. Technical Features
   [List of Technical Features]

3. Feature Comparison Table
   [Comparison Table]

4. Invalidation Commentary
   [Analysis of Invalidation Grounds]

5. Invalidation Conclusion
   [Comprehensive Conclusion]

6. Search Strategy
   [Search Strategy Table]

7. List of Related Patents
   [List of 50 Patents]
```
**Disclaimer (Must be indicated on the first page of the report)**
Refer to 'references/disclaimer.md.'

**Use the docx skill to generate a patent invalidation search report**:
1. Call the docx skill to create a professionally formatted Word document.
2. Include a cover page, table of contents, and main text.
3. Standardize table formatting.
4. Save as a `.docx` file and provide it to the user.

## Tool Usage
### Browser Retrieval
```
Use the browser_use tool:
1. Open the Google Patents website: action=open, url=https://patents.google.com
2. Enter search queries: Input keyword combinations in the search box.
3. Obtain results: Use snapshot to get page content.
4. Flip pages to get more results.
```

### Document Generation
```
Use the docx skill:
1. Create the document structure.
2. Populate content for each chapter.
3. Insert tables and format them.
4. Save and provide the file to the user.
```

## Notes
1. **Objectivity**: All judgments must be based on evidence and avoid subjective assumptions.
2. **Accuracy**: Patent information must be accurate and error-free.
3. **Completeness**: The report must include all necessary content.
4. **Professionalism**: Use standardized patent terminology.
5. **Timeliness**: Pay attention to the legal status of patents.

## Error Handling
- If Google Patents is inaccessible, automatically switch to other patent databases.
- If the search results are less than 50, state the reason and continue the analysis.
- If there are disputes in feature comparison, record them truthfully and explain.
- If common general knowledge cannot be determined, mark it for further verification.

## Quality Control Checklist (Internal Confirmation)
* [ ] Step 1: Has the filing date been confirmed? Has the solution been confirmed by the user as independent and complete?
* [ ] Step 3: Does the feature disassembly fully cover the target claims?
* [ ] Step 4: Are the publication dates of all search results earlier than the filing date of the target patent?
* [ ] Step 7: Has a clear evidence combination scheme (e.g., E1+E2) been provided?

## Reference Documents
- references/search-strategies.md: Search strategies and keyword templates for common technical fields