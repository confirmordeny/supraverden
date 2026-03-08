# Data Dictionary

| Property | Title | Data type | Length | Requirement | Description | Permissible values | Validation rules | Example |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Abbreviation | Abbreviation |  |  | optional | Abbreviation used by the organisation itself or in common use |  |  |  |
| Assessment_against_FATF_definition | Assessment_against_FATF_definition |  |  | strongly recommended | The repo's assessment as to whether the organisation is likely to satisfy the FATF definition of International organisation. | Included, Excluded |  |  |
| Basis_for_assessment | Basis_for_assessment | text |  | strongly recommended | The code for the basis for repo's assessment as to whether the organisation is likely to satisfy the FATF definition of International organisation. |  | begins with "B" followed by two digits, B00 is not valid. |  |
| Country | Country code | text |  | mandatory | Country code for the organisation. EU is used for European Union entities and ZZ is used for all other international organisations. | EU, ZZ | must consist of two uppercase letters |  |
| Name_en | Name_en | text |  | mandatory | The full formal name of the organisation in English. Typically, "the" is omitted from the start. |  |  |  |
| OpenSanctions_id | OpenSanctions_id | OpenSanctions ID |  | mandatory | OpenSanctions ID code from opensanctions.org |  | no spaces |  |
| Org_family | Organisation family |  |  | mandatory (can be "none") | The family of organisations to which the organisation belongs. |  |  |  |
| Treaty_url | Treaty url | URL |  | optional | The URL of the treaty that created or reconstituted the organisation. |  | begins with "http", no spaces |  |
| Type | Type | text |  | optional | The type of the international organisation from a legal perspective. |  |  |  |
| Wikidata_code | Wikidata code | text |  | optional | Wikidata property code for the organisation |  | starts with "Q" remaining characters are digits 0-9. |  |
| Year_established | Year established | integer |  | optional | The calendar year in which the organisation was established based on the Gregorian calendar. |  | no earlier than 1810, no later than the current year |  |