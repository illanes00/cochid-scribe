export type TemplateDocType = 'paper' | 'thesis' | 'policy'

export interface DocumentTemplate {
  id: string
  title: string
  description: string
  doc_type: TemplateDocType
  markdown: string
}

export const templates: DocumentTemplate[] = [
  {
    id: 'policy-brief',
    title: 'Policy Brief',
    description: 'One-page policy brief with sections for context and recommendations.',
    doc_type: 'policy',
    markdown: `# Executive Summary

## Context

## Key Findings
- 

## Recommendations
- 

## Risks & Trade-offs
- 

## Sources
`,
  },
  {
    id: 'research-paper',
    title: 'Research Paper',
    description: 'Academic paper outline with standard sections.',
    doc_type: 'paper',
    markdown: `# Title

## Abstract

## Introduction

## Literature Review

## Methodology

## Results

## Discussion

## Conclusion

## References
`,
  },
  {
    id: 'slide-deck',
    title: 'Slide Deck',
    description: 'Presentation outline ready for export to Slides.',
    doc_type: 'policy',
    markdown: `# Slide 1: Title

# Slide 2: Problem

- 

# Slide 3: Evidence

- 

# Slide 4: Proposal

- 

# Slide 5: Impact

- 
`,
  },
]

export default templates
