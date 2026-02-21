# Data Dictionary

| Property | Title | Data type | Length | Requirement | Description | Permissible values | Validation rules | Example |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Abbreviation | Abbreviation | text | 10 | optional | Abbreviation used by the organisation itself or in common use |  |  | NATO, UN |
| Country | Country | text | 2 | mandatory | Country code for the organisation. EU is used for European Union entities and ZZ is used for all other international organisations. | EU, ZZ |  | EU, ZZ |
| Org_family | Organisation family | text | 100 | mandatory (can be "none") | The family of organisations to which the organisation belongs. |  |  | African Union entities |
| Treaty_url | Treaty url | URL | 2048 | optional | The URL of the treaty that created or reconstituted the organisation. |  |  | https://iho.int/uploads/user/pubs/misc/M1_Separatedocs/Convention_new_EN.pdf |
| Wikidata_code | Wikidata code | text | 15 | optional | Wikidata property code for the organisation |  | starts with "Q" remaining characters are digits 0-9. | Q674182 |