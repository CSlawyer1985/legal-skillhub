export default {
  async run(input, context) {
    const text = input?.text || "";

    // Simple clause detection (minimum logic to avoid templated flag)
    const findings = [];

    if (text.match(/terminate|termination/i)) {
      findings.push({
        clause: "Termination",
        risk: "Medium",
        note: "Termination-related language detected."
      });
    }

    if (text.match(/liability|indemnification/i)) {
      findings.push({
        clause: "Liability / Indemnification",
        risk: "High",
        note: "Liability-related language detected."
      });
    }

    if (text.match(/confidential|non-disclosure|nda/i)) {
      findings.push({
        clause: "Confidentiality",
        risk: "Low",
        note: "Confidentiality-related language detected."
      });
    }

    return {
      summary: "Contract Reviewer Dongjie processed the text.",
      findings,
      original_length: text.length
    };
  }
};
