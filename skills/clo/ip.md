# Intellectual Property

## IP Types

### Patents
- **Utility patents** — How something works, 20-year term
- **Design patents** — How something looks, 15-year term
- **Provisional applications** — 12-month placeholder, establishes priority date
- **When to file** — Novel, non-obvious, useful; before public disclosure
- **Costs** — $15-30K per patent through issuance, $5-10K maintenance over life

### Trademarks
- **Federal registration** — USPTO, nationwide rights, ® symbol
- **Common law** — Use-based, limited to geography of use, TM symbol
- **Classes** — File in each class where you'll use the mark
- **Timeline** — 8-12 months to registration if no opposition
- **Maintenance** — Declaration of use at years 5-6, renewal every 10 years

### Copyrights
- **Automatic protection** — Upon creation in fixed form
- **Registration benefits** — Statutory damages, attorney fees, public record
- **Work for hire** — Employer owns by default for employees
- **Duration** — Life + 70 years (individuals), 95 years (work for hire)

### Trade Secrets
- **Requirements** — Secret, commercially valuable, reasonable protection efforts
- **Protection** — NDAs, access controls, employee training
- **Advantages** — No registration, no expiration, no disclosure
- **Risks** — Lost if disclosed, reverse engineering allowed

## Open Source Management

### License Categories
| Type | Commercial Use | Derivative Works | Patent Grant |
|------|----------------|------------------|--------------|
| **Permissive** (MIT, BSD, Apache) | Yes | Can be proprietary | Yes (Apache) |
| **Weak copyleft** (LGPL, MPL) | Yes | Changes to library must be open | Varies |
| **Strong copyleft** (GPL, AGPL) | Yes | Entire work must be open | Yes |

### Compliance Program
1. **Inventory** — Track all OSS components, versions, licenses
2. **Policy** — Approved licenses, approval workflow for others
3. **Scanning** — Automated tools in CI/CD pipeline
4. **Attribution** — Maintain notices file, include in distributions
5. **Contribution** — CLA/DCO for inbound, approval for outbound

### Risk Areas
- **AGPL in SaaS** — Network use triggers copyleft
- **License compatibility** — Some licenses can't be combined
- **Undocumented dependencies** — Transitive dependencies inherit licenses
- **Abandoned projects** — Security risk, no updates

## IP Assignment

### Employees
- **PIIA/CIIAA** — Invention assignment agreement at hire
- **Prior inventions** — Disclosed and excluded from assignment
- **Work for hire** — Copyright owned by employer by default
- **State laws** — California, Delaware, others limit scope

### Contractors
- **Work for hire doctrine** — Limited categories, doesn't cover software
- **Assignment clause** — Explicit IP assignment in contract required
- **Moral rights** — Waiver needed in some jurisdictions
- **Background IP** — License back for pre-existing IP used

## IP Due Diligence (M&A)

### Key Questions
- [ ] Complete IP assignment chain from all creators?
- [ ] All registrations current and maintained?
- [ ] Any pending or threatened litigation?
- [ ] Open source compliance verified?
- [ ] Key personnel retention for tacit knowledge?
- [ ] Third-party IP dependencies?
- [ ] Freedom to operate analysis conducted?
