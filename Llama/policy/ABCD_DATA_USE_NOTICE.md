# Third-Party Data Use, Attribution, and Licence Notice: ABCD Dataset

**Project:** EcomSafe / EcomSafeBench (Northeastern University, CS8674)
**Notice applies to:** the contents of `Llama/policy/` and every dataset, policy, or other material derived from them, including `Llama/data/`.
**Notice dated:** 4 October 2026

> **Not legal advice.** This notice records, in formal terms, how the project obtained and used a third-party dataset and how it meets that dataset's licence. It was prepared by the research team with AI assistance. It has not been reviewed by counsel. Before any public release or publication, confirm it with the course instructor and, where needed, Northeastern University's Office of the General Counsel.

---

## 1. Definitions

1.1 **"ABCD"** or **"the Dataset"**: the Action-Based Conversations Dataset, version 1.1, published by ASAPP Research at https://github.com/asappresearch/abcd. It includes the files `abcd_v1.1.json`, `guidelines.json`, `ontology.json`, and `kb.json`.

1.2 **"Licensor"**: the copyright holder named in the Dataset's licence, "ASAPP Research" (Copyright (c) 2021).

1.3 **"Licence"**: the MIT License under which the Licensor distributes the Dataset. Its full text is reproduced in Section 9.

1.4 **"Project"**: the EcomSafe research project and its benchmark, EcomSafeBench.

1.5 **"Derived Materials"**: any policy clause, design record, benchmark record, or other output of the Project that was produced with reference to the Dataset.

## 2. Source and retrieval

2.1 The four Dataset files above were retrieved from the Licensor's public GitHub repository on 1 October 2026. They are stored locally under `data/abcd/`.

2.2 The Licence file (`LICENSE`) and the Dataset's README, which contains the authors' requested citation, were retrieved from the same repository on 4 October 2026. They are stored as `data/abcd/ABCD_LICENSE` and `data/abcd/ABCD_README.md`.

2.3 The Project has not modified the original Dataset files.

## 3. Licence grant relied upon

3.1 The Project relies on the Licence's grant, "free of charge, to any person obtaining a copy", of the rights to "use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies". The grant is subject to the condition stated in Section 4.

3.2 No other licence, permission, or agreement with the Licensor has been sought or obtained. The Project claims no rights beyond those the Licence grants.

## 4. Conditions of the Licence and how the Project meets them

4.1 **Condition.** The Licence requires that "the above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software."

4.2 **Compliance.** The Project meets this condition as follows:

  (a) The Licence text and copyright notice are reproduced in full in Section 9 of this notice. They are also kept as `data/abcd/ABCD_LICENSE`.

  (b) Any distribution of Dataset files, in whole or in substantial part, will include the Licence text and copyright notice.

  (c) Any public release of Derived Materials will include this notice, or an equivalent attribution and the Licence text.

4.3 The largest Dataset file (`abcd_v1.1.json`, approximately 121 MB) is excluded from the Project's version control. The Project's repository does not redistribute the Dataset's conversation records.

## 5. Nature and extent of use

5.1 **Policy derivation (`Llama/policy/`).** The Dataset's agent guidelines (`guidelines.json`), action ontology (`ontology.json`), and canonical action sequences (`kb.json`) were given to the language model `meta-llama/Llama-3.2-3B-Instruct`. The model was instructed to extract enforceable rules and to state them **in its own words**.

  - An automated check rejected any clause that shares six or more consecutive words with the guideline text.
  - Each resulting clause is tagged with its source: `ABCD-guidelines`, `ABCD-ontology`, or `authored`.
  - Clauses tagged `ABCD-guidelines` also name the Dataset procedure they derive from.
  - Clauses tagged `authored` have no Dataset source. They cover product domains the Dataset does not address: pharmaceuticals, groceries, and financial products.

5.2 **Seed provenance (`Llama/data/`).** Benchmark records may cite a Dataset conversation by its numeric `convo_id`, as a provenance reference. No Dataset conversation text is copied into any benchmark record.

5.3 **No use of personal data.** The Dataset's conversation scenarios contain customer names, email addresses, telephone numbers, and postal addresses. The Project understands these to be fictional values created for the Dataset. The Project did not extract, copy, or use any of these values, and it does not process them for any purpose.

5.4 **Purpose.** All use is for non-commercial academic research and coursework. The research evaluates the safety of AI customer-service agents.

## 6. Disclaimer of warranty and liability (passed through from the Licence)

6.1 The Dataset is provided by the Licensor "AS IS", without warranty of any kind, as stated in the Licence. The Project makes no representation about the Dataset's accuracy, completeness, or fitness for any purpose.

6.2 Derived Materials are research artefacts generated in part by a language model. They are provided without warranty. They do not represent the policies of any real retailer.

## 7. No endorsement or affiliation

7.1 The Project is not affiliated with, sponsored by, or endorsed by ASAPP, Inc., ASAPP Research, or the Dataset's authors.

7.2 Nothing in the Derived Materials should be read as the Licensor's or the authors' policy, opinion, or endorsement.

7.3 The fictional retailer in the Dataset, and any policy derived from it, do not describe any real company.

## 8. Attribution and citation

8.1 Any publication, report, or release that uses Derived Materials will cite the Dataset in the form its authors request:

```bibtex
@inproceedings{chen2021abcd,
    title     = "Action-Based Conversations Dataset: A Corpus for Building More In-Depth Task-Oriented Dialogue Systems",
    author    = "Chen, Derek and Chen, Howard and Yang, Yi and Lin, Alex and Yu, Zhou",
    booktitle = "Proceedings of the 2021 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, {NAACL-HLT} 2021",
    month     = jun,
    year      = "2021",
    address   = "Online",
    publisher = "Association for Computational Linguistics",
    url       = "https://www.aclweb.org/anthology/2021.naacl-main.239",
    pages     = "3002--3017"
}
```

8.2 **Related third-party terms (for the team to confirm).** The Derived Materials in `Llama/` were generated with Meta's Llama 3.2. Use of that model is governed by the **Llama 3.2 Community License Agreement** and Meta's **Acceptable Use Policy**, which the account holder accepted when downloading the model. Those terms are separate from, and in addition to, the Licence above. Before publishing any `Llama/` output, the team should review them, in particular any attribution requirements for materials distributed with or derived from Llama.

## 9. Full text of the Licence

```
MIT License

Copyright (c) 2021 ASAPP Research

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
