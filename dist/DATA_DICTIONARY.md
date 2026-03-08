# Data Dictionary

| Property | Title | Data type | Length | Requirement | Description | Permissible values | Validation rules | Example |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| _record_policy |  |  |  |  |  |  |  |  |
| _variant_policy |  |  |  |  |  |  |  |  |
| Abbreviation | Abbreviation |  |  | optional | Abbreviation for the organisation in the language indicated by suffix. |  |  |  |
| Abbreviation_former | Former abbreviation |  |  | optional | Former abbreviation of the organisation in the language indicated by suffix. |  |  |  |
| Abbreviation_other | Other abbreviation |  |  | optional | Alternative abbreviation of the organisation in the language indicated by suffix. |  |  |  |
| Assessment_against_FATF_definition | Assessment_against_FATF_definition |  |  | strongly recommended | The repo's assessment as to whether the organisation is likely to satisfy the FATF definition of International organisation. | Included, Excluded |  |  |
| Basis_for_assessment | Basis_for_assessment |  |  | strongly recommended | The code for the basis for repo's assessment as to whether the organisation is likely to satisfy the FATF definition of International organisation. |  |  |  |
| Country | Country code |  |  | mandatory | Country code for the organisation. EU is used for European Union entities and ZZ is used for all other international organisations. | EU, ZZ |  |  |
| Entity_type | Entity type |  |  | mandatory | High-level classification of the entity. | International organisation |  |  |
| Headquarters | Headquarters |  |  | recommended | Location of the organisation's headquarters. |  |  |  |
| Immunity_url | Immunity url |  |  | strongly recommended | URL to a source for privileges and immunities applicable to the organisation. |  |  |  |
| LEI | Legal Entity Identifier |  |  | optional | 20-character Legal Entity Identifier (ISO 17442) for the organisation. |  |  |  |
| LEI_bic | LEI BIC |  |  | optional | BIC associated with the LEI record, where available. |  |  |  |
| LEI_category | LEI category |  |  | optional | LEI entity category from the LEI reference record. | GENERAL, INTERNATIONAL_ORGANIZATION, RESIDENT_GOVERNMENT_ENTITY, FUND |  |  |
| LEI_hq_address | LEI headquarters address |  |  | optional | Headquarters address from the LEI reference record. |  |  |  |
| LEI_jurisdiction | LEI jurisdiction |  |  | optional | Jurisdiction code reported in the LEI record. |  |  |  |
| LEI_legal_form | LEI legal form |  |  | optional | Legal form string from the LEI reference record. |  |  |  |
| LEI_status | LEI status |  |  | optional | LEI registration status from the LEI reference record, as at March 2026. | ACTIVE, INACTIVE, LAPSED, RETIRED, ANNULLED, MERGED, DUPLICATE, PENDING_TRANSFER, PENDING_ARCHIVAL, ISSUED |  |  |
| Name | Name |  |  | mandatory | The full formal name of the organisation in the language indicated by suffix. |  |  |  |
| Name_former | Former name |  |  | optional | A former official name of the organisation in the language indicated by suffix. |  |  |  |
| Name_other | Other name |  |  | optional | Alternative name of the organisation in the language indicated by suffix. |  |  |  |
| Notes | Notes |  |  | optional | Free-text notes for context, caveats, or editorial clarifications in the language indicated by suffix. |  |  |  |
| OpenSanctions_id | OpenSanctions_id |  |  | mandatory | OpenSanctions ID code from opensanctions.org. If no identifier exists, [No code found.] may be used. |  |  |  |
| Org_family | Organisation family |  |  | mandatory (can be "none") | The family of organisations to which the organisation belongs. |  |  |  |
| SPRVD_id | SPRVD_id |  |  | mandatory (primary key) | Unique identifier assigned by this repository to each organisation record. |  |  |  |
| Source | Source |  |  | recommended | Source reference for the record data. May be a URL, citation, publication title, or other textual reference. |  |  |  |
| Treaty_url | Treaty url |  |  | optional | The URL of the treaty that created or reconstituted the organisation. |  |  |  |
| Type | Type |  |  | optional | The type of the international organisation from a legal perspective. |  |  |  |
| Wikidata_code | Wikidata code |  |  | optional | Wikidata property code for the organisation. If no identifier exists, [No code found.] may be used. |  |  |  |
| Year_established | Year established |  |  | optional | The calendar year in which the organisation was established based on the Gregorian calendar. |  |  |  |