# Data Dictionary

## Field Index

- [`Abbreviation`](#field-abbreviation)
- [`Abbreviation_former`](#field-abbreviation_former)
- [`Abbreviation_other`](#field-abbreviation_other)
- [`Assessment_against_FATF_definition`](#field-assessment_against_fatf_definition)
- [`Basis_for_assessment`](#field-basis_for_assessment)
- [`Country`](#field-country)
- [`Entity_type`](#field-entity_type)
- [`Headquarters`](#field-headquarters)
- [`Immunity_url`](#field-immunity_url)
- [`LEI`](#field-lei)
- [`LEI_bic`](#field-lei_bic)
- [`LEI_category`](#field-lei_category)
- [`LEI_hq_address`](#field-lei_hq_address)
- [`LEI_jurisdiction`](#field-lei_jurisdiction)
- [`LEI_legal_form`](#field-lei_legal_form)
- [`LEI_status`](#field-lei_status)
- [`Name`](#field-name)
- [`Name_zh`](#field-name_zh)
- [`Name_former`](#field-name_former)
- [`Name_other`](#field-name_other)
- [`Notes`](#field-notes)
- [`OpenSanctions_id`](#field-opensanctions_id)
- [`Org_family`](#field-org_family)
- [`SPRVD_id`](#field-sprvd_id)
- [`Source`](#field-source)
- [`Treaty_url`](#field-treaty_url)
- [`Type`](#field-type)
- [`VAT_number`](#field-vat_number)
- [`Wikidata_code`](#field-wikidata_code)
- [`Website`](#field-website)
- [`Year_established`](#field-year_established)

## Record Policy

| Key | Value |
| --- | --- |
| `required_fields` | SPRVD_id, Entity_type, Country, Name_en |
| `source_required_for` | Type |

## Variant Policy

| Key | Value |
| --- | --- |
| `language_suffixes` | en, fr, es, de, pt, ru, uk, zh |
| `index_suffixes` | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20 |
| `variant_usage` | Variant fields may use language suffixes and index numbers together, e.g. Name_other_1_en. |
| `applies_to` | Name, Abbreviation, Abbreviation_former, Abbreviation_other, Name_former, Name_other, Notes |

<a id="field-abbreviation"></a>
## `Abbreviation`

| Attribute | Value |
| --- | --- |
| `Title` | Abbreviation |
| `Data_type` | text |
| `Minimum_length` | 2 |
| `Maximum_length` | 50 |
| `Requirement` | optional |
| `Description` | Abbreviation for the organisation in the language indicated by suffix. |
| `Examples` | EU, UN |

<a id="field-abbreviation_former"></a>
## `Abbreviation_former`

| Attribute | Value |
| --- | --- |
| `Title` | Former abbreviation |
| `Data_type` | text |
| `Minimum_length` | 2 |
| `Maximum_length` | 50 |
| `Requirement` | optional |
| `Description` | Former abbreviation of the organisation in the language indicated by suffix. |
| `Example_source` | Organisation of Islamic Cooperation |
| `Examples` | OIC |

<a id="field-abbreviation_other"></a>
## `Abbreviation_other`

| Attribute | Value |
| --- | --- |
| `Title` | Other abbreviation |
| `Data_type` | text |
| `Minimum_length` | 2 |
| `Maximum_length` | 50 |
| `Requirement` | optional |
| `Description` | Alternative abbreviation of the organisation in the language indicated by suffix. |
| `Example_source` | African Intellectual Property organisation |
| `Examples` | OAPI |

<a id="field-assessment_against_fatf_definition"></a>
## `Assessment_against_FATF_definition`

| Attribute | Value |
| --- | --- |
| `Title` | Assessment_against_FATF_definition |
| `Data_type` | text |
| `Requirement` | strongly recommended |
| `Description` | The repo's assessment as to whether the organisation is likely to satisfy the FATF definition of International organisation. |
| `Permissible values` | Included, Excluded |
| `Examples` | Included |

<a id="field-basis_for_assessment"></a>
## `Basis_for_assessment`

| Attribute | Value |
| --- | --- |
| `Title` | Basis_for_assessment |
| `Data_type` | text |
| `Minimum_length` | 2 |
| `Maximum_length` | 3 |
| `Requirement` | strongly recommended |
| `Description` | The code for the basis for repo's assessment as to whether the organisation is likely to satisfy the FATF definition of International organisation. |
| `Validation_summary` | begins with "B" followed by one or two digits; B00 is not valid. |
| `Examples` | B22 |
| `Validation_rules` | `- rule: regex   pattern: ^B\d{1,2}$ - rule: disallow_values   values:   - B00` |

<a id="field-country"></a>
## `Country`

| Attribute | Value |
| --- | --- |
| `Title` | Country code |
| `Data_type` | text |
| `Minimum_length` | 2 |
| `Maximum_length` | 2 |
| `Requirement` | mandatory |
| `Description` | Country code for the organisation. EU is used for European Union entities and ZZ is used for all other international organisations. |
| `Permissible values` | EU, ZZ |
| `Validation_summary` | must consist of two uppercase letters. |
| `Examples` | EU, ZZ |
| `Property` | Country |
| `Validation_rules` | `- rule: regex   pattern: ^[A-Z]{2}$` |

<a id="field-entity_type"></a>
## `Entity_type`

| Attribute | Value |
| --- | --- |
| `Title` | Entity type |
| `Data_type` | text |
| `Minimum_length` | 5 |
| `Maximum_length` | 50 |
| `Requirement` | mandatory |
| `Description` | High-level classification of the entity. |
| `Permissible values` | International organisation |
| `Example_source` | European Union |
| `Examples` | International organisation |

<a id="field-headquarters"></a>
## `Headquarters`

| Attribute | Value |
| --- | --- |
| `Title` | Headquarters |
| `Data_type` | text |
| `Minimum_length` | 2 |
| `Maximum_length` | 200 |
| `Requirement` | recommended |
| `Description` | Location of the organisation's headquarters. |
| `Example_source` | UNESCO |
| `Examples` | Paris, France |

<a id="field-immunity_url"></a>
## `Immunity_url`

| Attribute | Value |
| --- | --- |
| `Title` | Immunity url |
| `Data_type` | url |
| `Minimum_length` | 12 |
| `Maximum_length` | 2048 |
| `Requirement` | strongly recommended |
| `Description` | URL to a source for privileges and immunities applicable to the organisation. |
| `Validation_summary` | must begin with "http" and contain no spaces. |
| `Examples` | https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32003R0058 |
| `Validation_rules` | `- rule: starts_with   value: http - rule: no_spaces` |

<a id="field-lei"></a>
## `LEI`

| Attribute | Value |
| --- | --- |
| `Title` | Legal Entity Identifier |
| `Data_type` | text |
| `Minimum_length` | 20 |
| `Maximum_length` | 20 |
| `Requirement` | optional |
| `Description` | 20-character Legal Entity Identifier (ISO 17442) for the organisation. |
| `Validation_summary` | exactly 20 characters, uppercase letters A-Z and digits 0-9 only, no spaces. |
| `Example_source` | UNESCO |
| `Examples` | 549300UOQ4N8CBASRY79 |
| `Validation_rules` | `- rule: exact_length   length: 20 - rule: regex   pattern: ^[A-Z0-9]{20}$ - rule: no_spaces` |

<a id="field-lei_bic"></a>
## `LEI_bic`

| Attribute | Value |
| --- | --- |
| `Title` | LEI BIC |
| `Data_type` | text |
| `Minimum_length` | 8 |
| `Maximum_length` | 11 |
| `Requirement` | optional |
| `Description` | BIC associated with the LEI record, where available. |
| `Multi_value` | True |
| `Validation_summary` | uppercase letters A-Z and digits 0-9 only; either blank/null or 8 or 11 characters. |
| `Example_source` | UNESCO |
| `Examples` | UNESFRP2XXX |
| `Validation_rules` | `- rule: regex   pattern: ^[A-Z0-9]{8}([A-Z0-9]{3})?$   allow_blank: true` |

<a id="field-lei_category"></a>
## `LEI_category`

| Attribute | Value |
| --- | --- |
| `Title` | LEI category |
| `Data_type` | text |
| `Requirement` | optional |
| `Description` | LEI entity category from the LEI reference record. |
| `Permissible values` | GENERAL, INTERNATIONAL_ORGANIZATION, RESIDENT_GOVERNMENT_ENTITY, FUND |
| `Examples` | INTERNATIONAL_ORGANIZATION |

<a id="field-lei_hq_address"></a>
## `LEI_hq_address`

| Attribute | Value |
| --- | --- |
| `Title` | LEI headquarters address |
| `Data_type` | text |
| `Minimum_length` | 5 |
| `Maximum_length` | 512 |
| `Requirement` | optional |
| `Description` | Headquarters address from the LEI reference record. |
| `Examples` | 7 Placé de Fontenoy, Paris, 75007, FR |

<a id="field-lei_jurisdiction"></a>
## `LEI_jurisdiction`

| Attribute | Value |
| --- | --- |
| `Title` | LEI jurisdiction |
| `Data_type` | text |
| `Minimum_length` | 2 |
| `Maximum_length` | 10 |
| `Requirement` | optional |
| `Description` | Jurisdiction code reported in the LEI record. |
| `Examples` | UN |

<a id="field-lei_legal_form"></a>
## `LEI_legal_form`

| Attribute | Value |
| --- | --- |
| `Title` | LEI legal form |
| `Data_type` | text |
| `Minimum_length` | 2 |
| `Maximum_length` | 200 |
| `Requirement` | optional |
| `Description` | Legal form string from the LEI reference record. |
| `Examples` | United Nations Specialized Agency |

<a id="field-lei_status"></a>
## `LEI_status`

| Attribute | Value |
| --- | --- |
| `Title` | LEI status |
| `Data_type` | text |
| `Requirement` | optional |
| `Description` | LEI registration status from the LEI reference record, as at March 2026. |
| `Permissible values` | ACTIVE, INACTIVE, LAPSED, RETIRED, ANNULLED, MERGED, DUPLICATE, PENDING_TRANSFER, PENDING_ARCHIVAL, ISSUED |
| `Examples` | ACTIVE |

<a id="field-name"></a>
## `Name`

| Attribute | Value |
| --- | --- |
| `Title` | Name |
| `Data_type` | text |
| `Minimum_length` | 4 |
| `Maximum_length` | 200 |
| `Requirement` | mandatory |
| `Description` | The full formal name of the organisation in the language indicated by suffix. |
| `Examples` | European Union, United Nations |

<a id="field-name_zh"></a>
## `Name_zh`

| Attribute | Value |
| --- | --- |
| `Title` | Name (Chinese) |
| `Data_type` | text |
| `Minimum_length` | 2 |
| `Maximum_length` | 200 |
| `Requirement` | optional |
| `Description` | Chinese-script full name of the organisation; shorter lengths are valid for logographic names. |
| `Examples` | 联合国 |

<a id="field-name_former"></a>
## `Name_former`

| Attribute | Value |
| --- | --- |
| `Title` | Former name |
| `Data_type` | text |
| `Minimum_length` | 2 |
| `Maximum_length` | 200 |
| `Requirement` | optional |
| `Description` | A former official name of the organisation in the language indicated by suffix. |
| `Example_source` | Organization of American States |
| `Examples` | Pan-American Union |

<a id="field-name_other"></a>
## `Name_other`

| Attribute | Value |
| --- | --- |
| `Title` | Other name |
| `Data_type` | text |
| `Minimum_length` | 2 |
| `Maximum_length` | 200 |
| `Requirement` | optional |
| `Description` | Alternative name of the organisation in the language indicated by suffix. |
| `Examples` | Council of the EU |

<a id="field-notes"></a>
## `Notes`

| Attribute | Value |
| --- | --- |
| `Title` | Notes |
| `Data_type` | text |
| `Minimum_length` | 0 |
| `Maximum_length` | 2000 |
| `Requirement` | optional |
| `Description` | Free-text notes for context, caveats, or editorial clarifications in the language indicated by suffix. |
| `Example_source` | International Commission for the Protection of the Danube River |
| `Examples` | Not to be confused with the Danube Commission. |

<a id="field-opensanctions_id"></a>
## `OpenSanctions_id`

| Attribute | Value |
| --- | --- |
| `Title` | OpenSanctions_id |
| `Data_type` | text |
| `Minimum_length` | 10 |
| `Maximum_length` | 50 |
| `Requirement` | mandatory |
| `Description` | OpenSanctions ID code from opensanctions.org. If no identifier exists, [No code found.] may be used. |
| `Validation_summary` | no spaces, except [No code found.]. |
| `Examples` | bic-ESMAFRP2, NK-Ubo23KznV2pvcXMiQkTmvd, [No code found.] |
| `Validation_rules` | `- rule: no_spaces   allow_values:   - '[No code found.]'` |

<a id="field-org_family"></a>
## `Org_family`

| Attribute | Value |
| --- | --- |
| `Title` | Organisation family |
| `Data_type` | text |
| `Maximum_length` | 100 |
| `Requirement` | mandatory (can be "none") |
| `Description` | The family of organisations to which the organisation belongs. |
| `Examples` | African Union entities |
| `Property` | Org_family |

<a id="field-sprvd_id"></a>
## `SPRVD_id`

| Attribute | Value |
| --- | --- |
| `Title` | SPRVD_id |
| `Data_type` | text |
| `Minimum_length` | 12 |
| `Maximum_length` | 12 |
| `Requirement` | mandatory (primary key) |
| `Description` | Unique identifier assigned by this repository to each organisation record. |
| `Validation_summary` | must match SPRVD0 followed by 6 digits; final digit is a check digit. |
| `Examples` | SPRVD0688028 |
| `Validation_rules` | `- rule: regex   pattern: ^SPRVD0\d{6}$` |

<a id="field-source"></a>
## `Source`

| Attribute | Value |
| --- | --- |
| `Title` | Source |
| `Data_type` | text |
| `Minimum_length` | 3 |
| `Maximum_length` | 2048 |
| `Requirement` | recommended |
| `Description` | Source reference for the record data. May be a URL, citation, publication title, or other textual reference. |
| `Example_source` | UNESCO |
| `Examples` | https://www.un.org/en/about-us/specialized-agencies |

<a id="field-treaty_url"></a>
## `Treaty_url`

| Attribute | Value |
| --- | --- |
| `Title` | Treaty url |
| `Data_type` | url |
| `Minimum_length` | 12 |
| `Maximum_length` | 2048 |
| `Requirement` | optional |
| `Description` | The URL of the treaty that created or reconstituted the organisation. |
| `Validation_summary` | must begin with "http" and contain no spaces. |
| `Examples` | https://iho.int/uploads/user/pubs/misc/M1_Separatedocs/Convention_new_EN.pdf |
| `Property` | Treaty_url |
| `Validation_rules` | `- rule: starts_with   value: http - rule: no_spaces` |

<a id="field-type"></a>
## `Type`

| Attribute | Value |
| --- | --- |
| `Title` | Type |
| `Data_type` | text |
| `Minimum_length` | 5 |
| `Maximum_length` | 50 |
| `Requirement` | optional |
| `Description` | The type of the international organisation from a legal perspective. |
| `Examples` | EU decentralised agency, EU executive agency |
| `Property` | Type |

<a id="field-vat_number"></a>
## `VAT_number`

| Attribute | Value |
| --- | --- |
| `Title` | VAT number |
| `Data_type` | text |
| `Minimum_length` | 4 |
| `Maximum_length` | 20 |
| `Requirement` | optional |
| `Description` | VAT number(s) sourced from Wikidata (property P3608), where available. |
| `Multi_value` | True |
| `Validation_summary` | starts with a two-letter country code followed by letters/digits. |
| `Examples` | DE123456789 |
| `Validation_rules` | `- rule: regex   pattern: ^[A-Z]{2}[A-Z0-9*+]+$` |

<a id="field-wikidata_code"></a>
## `Wikidata_code`

| Attribute | Value |
| --- | --- |
| `Title` | Wikidata code |
| `Data_type` | text |
| `Maximum_length` | 15 |
| `Requirement` | optional |
| `Description` | Wikidata property code for the organisation. If no identifier exists, [No code found.] may be used. |
| `Validation_summary` | starts with "Q"; remaining characters are digits 0-9, except [No code found.]. |
| `Examples` | Q674182, [No code found.] |
| `Property` | Wikidata_code |
| `Validation_rules` | `- rule: regex   pattern: ^Q\d+$   allow_values:   - '[No code found.]'` |

<a id="field-website"></a>
## `Website`

| Attribute | Value |
| --- | --- |
| `Title` | Website |
| `Data_type` | url |
| `Minimum_length` | 12 |
| `Maximum_length` | 2048 |
| `Requirement` | optional |
| `Description` | Official website URL sourced from Wikidata (property P856), where available. |
| `Validation_summary` | must begin with "http" and contain no spaces. |
| `Examples` | https://www.un.org/ |
| `Property` | Website |
| `Validation_rules` | `- rule: starts_with   value: http - rule: no_spaces` |

<a id="field-year_established"></a>
## `Year_established`

| Attribute | Value |
| --- | --- |
| `Title` | Year established |
| `Data_type` | integer |
| `Maximum_length` | 4 |
| `Requirement` | optional |
| `Description` | The calendar year in which the organisation was established based on the Gregorian calendar. |
| `Validation_summary` | no earlier than 1810, no later than the current year. |
| `Examples` | 1993 |
| `Property` | Year_established |
| `Validation_rules` | `- rule: year_range   min: 1810   max_current_year: true` |
