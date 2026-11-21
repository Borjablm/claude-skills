# Primary legal sources and traps

Cite the instrument. Use guidance for practice, forms, fees and contacts, and say it is guidance.

## Where the law is
| Jurisdiction | Primary text | Notes |
|---|---|---|
| EU | eur-lex.europa.eu (CELEX or ELI URL; use the consolidated version where one exists) | Directives bind only once transposed. Note the transposition date and look for the national instrument |
| Republic of Ireland | irishstatutebook.ie (ELI `/eli/<year>/si/<no>/made/en/print` for S.I.s); revised Acts from the Law Reform Commission (revisedacts.lawreform.ie) | S.I.s on the statute book are as made. Search the statute book for later S.I.s that amend them. Some fetchers get 403; a plain HTTP client with a browser user agent worked |
| Northern Ireland | legislation.gov.uk (`/nisr/<year>/<no>`, `/nisi/` for Orders) | Shows a revised version with "outstanding changes" warnings; read them |
| UK-wide (incl. NI) | legislation.gov.uk (`/uksi/`, `/ukpga/`); HMRC rates on gov.uk | Landfill tax rates are set annually; the gov.uk rates page lists the next year too |
| England and Wales | legislation.gov.uk (`/uksi/`, `/wsi/`); regulators EA and NRW | Wales has its own landfill disposals tax (gov.wales) |
| Scotland | legislation.gov.uk (`/ssi/`, `/asp/`); SEPA; revenue.scot for Scottish Landfill Tax and the annual rate order | Waste authorisations sit under the Environmental Authorisations (Scotland) Regulations 2018 (SSI 2018/219). legislation.gov.uk shows the Waste Management Licensing (Scotland) Regulations 2011 as revoked (checked 21 Nov 2026), while a cold test found SEPA pages still describing them. Check which regime applies on the scan date |
| Between UK nations | Each nation's carrier and duty-of-care rules | Moving waste from Scotland to England is not a transfrontier shipment, but each nation registers carriers separately. Whether a carrier registered in one nation needs registering in another is a call question for the regulators |
| Other EU states | The national official journal (BOE Spain, Légifrance France, wetten.overheid.nl Netherlands, Belgisch Staatsblad / Moniteur belge) | Regional layers in Spain and Belgium |
| Courts | curia.europa.eu (CJEU) | Waste-status tests (intention to discard, certainty of reuse) come from case law |

## Traps seen in testing (carpet tiles, island of Ireland, Nov 2026)
1. **Stale recall.** A no-web answer gave the Irish landfill levy as EUR 75/t "since 2013". It had been EUR 85/t since 1 Sep 2023 (S.I. 398/2023).
2. **Right topic, wrong instrument.** The same answer cited the NI duty-of-care regulations (SR 2013/255) for carrier registration, which sits in SR 1999/362.
3. **As-made text.** S.I. 821/2007 as made caps residual waste from a Class 10 site at 7,500 t; S.I. 86/2008 changed it to 15% of intake. Search for amending instruments before quoting a threshold.
4. **Guidance behind the law.** DAERA's waste-shipment page (Nov 2026) still described Regulation (EC) 1013/2006, replaced by Regulation (EU) 2024/1157 from 21 May 2026. A fee page showed a newer fee than an agent had found elsewhere (GBP 191, not GBP 180).
5. **Scope by product code.** EU textile EPR (Directive (EU) 2025/1892, Annex IVc) lists CN codes. Carpets (chapter 57) are not in it. Always read the annex.
6. **Two systems on one territory.** In Northern Ireland, UK law governs permits and tax, while EU waste-shipment rules apply to NI-EU movements under the Windsor Framework. Movements NI to Great Britain were the one question neither run could settle.
7. **Suspended services.** The NI regulator suspended its end-of-waste submission service in Feb 2025. A route that exists in law may not be open in practice.
8. **Guessed citations.** A cold test recalled "SSI 2005/625" as Scotland's hazardous-waste regulations; it is an animal-health order. Find instruments by search, never by memory.

## Questions the desk scan cannot close
- Which waste code the regulator expects for the separately collected product (it can change which levy timetable applies).
- Whether cleaning or grading the product fits an existing exemption or needs a full permit.
- Whether a clean, sorted load ships as green-list (Annex VII) or needs notification, for each border.
- Whether direct reuse (never discarded, handed over for certain reuse) is accepted as outside waste law, and what records the regulator wants.
