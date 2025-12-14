# AIMS Data Model Reconciliation Report
**Date:** 2025-12-07 17:50:43

## 1. Model vs Parquet Files
| Table | Status | Rows | Size | Details |
|---|---|---|---|---|
| Routes | ⚠️ MISMATCH | 33 | 5.99 KB | Missing: COPIEDFROM |
| Phases | ⚠️ MISMATCH | 6 | 2.46 KB | Missing: LATESTVOLUMERECORD |
| Stages | ⚠️ MISMATCH | 8 | 2.53 KB | Missing: EIRTYPE |
| Owners | 🟡 AUDIT MISSING | 28 | 3.52 KB | Missing 6 Audit Cols (KINO) |
| RelationshipTypes | ⚠️ MISMATCH | 39 | 10.97 KB | Missing: DISPLAYASTABLE, DISPLAYREVERSEASTABLE, DISPLAYORDER... |
| LinkTypes | ⚠️ MISMATCH | 52 | 6.59 KB | Missing: DISPLAYORDER, DISPLAYASPRIMARYASSETIMAGE |
| Organisations | ⚠️ MISMATCH | 28 | 3.60 KB | Missing: PARENTKEYHIERARCHY, ISCONTRACTOR, DISPLAYORDER... |
| People | ⚠️ MISMATCH | 1898 | 108.85 KB | Missing: PREDECESSOR, SUCCEEDEDON, CREATEUSERPROCESS... |
| Users | 🔴 MISSING | - | - | File aims_users.parquet not found |
| AssetClasses | ⚠️ MISMATCH | 5644 | 624.78 KB | Missing: LatestLog, GROUPINGCLASSFORHIERARCHYREPOR, OLDHIERARCHYENTITY... |
| AttributeGroups | ⚠️ MISMATCH | 80 | 5.12 KB | Missing: DISPLAYORDER, DEFAULTVIEW, DEFINESMATRIX... |
| Attributes | ⚠️ MISMATCH | 6533 | 400.97 KB | Missing: ATTRIBUTELEVEL, GRAPHCOLOUR, LINEARATTRIBUTE... |
| AssetClassAttributes | ⚠️ MISMATCH | 131311 | 2.46 MB | Missing: REQUIREDATSTAGEOLD, AVAILABLEFROMSTAGEOLD, CREATEDBYUPDATE... |
| AssetClassRelationships | ⚠️ MISMATCH | 49515 | 1013.33 KB | Missing: REQUIREDATSTAGEOLD, CREATEDBYUPDATE, UUID |
| AttributeDomains | 🟡 AUDIT MISSING | 783 | 33.31 KB | Missing 6 Audit Cols (KINO) |
| AttributeDomainValues | ⚠️ MISMATCH | 3853 | 154.50 KB | Missing: ATTRIBUTENLR, LOWERBOUND, UPPERBOUND... |
| SecondaryAssetClassCodes | ⚠️ MISMATCH | 2329 | 67.08 KB | Missing: CREATEDBYUPDATE |
| SecondaryCodingSystems | 🔴 MISSING | - | - | File aims_secondarycodingsystems.parquet not found |
| AssetClassChangeLogs | ⚠️ MISMATCH | 15901 | 593.55 KB | Missing: CODE, NAME, CHAINAGE... |
| Assets | ⚠️ MISMATCH | 2217599 | 106.15 MB | Missing: ACCESSDBID, OWNERASSETATTRIBUTE, PHASEASSETATTRIBUTE... |
| AssetStatuses | 🔴 MISSING | - | - | File aims_assetstatuses.parquet not found |
| AssetLocations | ⚠️ MISMATCH | 2235262 | 93.27 MB | Missing: INSTANCEHIDDEN, STARTCHAINAGE, ENDCHAINAGE... |
| ChainageBaselines | 🔴 MISSING | - | - | File aims_chainagebaselines.parquet not found |
| Tracks | ✅ MATCH | 164 | 3.78 KB | Found 4 cols, 1 extra |
| Links | ⚠️ MISMATCH | 28631 | 1.09 MB | Missing: BASEDON, COPIEDFROM, FILEFIELD... |
| Relationships | ⚠️ MISMATCH | 1200269 | 44.67 MB | Missing: SOURCEASSETLOCATION, TARGETASSETLOCATION, PROCESSEDBY... |
| AssetHierarchyMap | ⚠️ MISMATCH | 4156827 | 129.12 MB | Missing: ID |
| AssetAttributes | ⚠️ MISMATCH | 60090986 | 1.34 GB | Missing: Location, TextDomainValue, LOCATION... |
| InformationPackages | ✅ MATCH | 0 | 1.07 KB | Found 10 cols, 9 extra |

## 2. Unmodeled Files (Extra Data)
These files exist in the data directory but are not defined in the Data Model.

| File Name | Guessed Table | Rows | Size |
|---|---|---|---|
| aims_activitydates.parquet | Activitydates | 325 | 24.12 KB |
| aims_assetconsents.parquet | Assetconsents | 6797 | 168.38 KB |
| aims_consentlinks.parquet | Consentlinks | 0 | 1.04 KB |
| aims_consentmilestones.parquet | Consentmilestones | 170346 | 1.18 MB |
| aims_consentmilestonetypes.parquet | Consentmilestonetypes | 34 | 1.57 KB |
| aims_consents.parquet | Consents | 5162 | 155.23 KB |
| aims_consenttypemilestones.parquet | Consenttypemilestones | 373 | 24.12 KB |
| aims_consenttypes.parquet | Consenttypes | 125 | 14.73 KB |
| aims_informationneedassetclass.parquet | Informationneedassetclass | 45 | 4.38 KB |
| aims_informationneedattributes.parquet | Informationneedattributes | 1337 | 39.27 KB |
| aims_informationneeddocs.parquet | Informationneeddocs | 0 | 1.49 KB |
| aims_informationneedgeometries.parquet | Informationneedgeometries | 45 | 9.80 KB |
| aims_informationneedlinks.parquet | Informationneedlinks | 1 | 3.99 KB |
| aims_informationneedpropchngs.parquet | Informationneedpropchngs | 2676 | 169.32 KB |
| aims_informationneeds.parquet | Informationneeds | 547 | 83.86 KB |
| aims_informationneedsourcedocs.parquet | Informationneedsourcedocs | 220 | 11.90 KB |
| aims_informationneedstatusupd.parquet | Informationneedstatusupd | 49 | 4.74 KB |
| aims_noncompliances.parquet | Noncompliances | 310 | 132.83 KB |
| aims_productassetclasses.parquet | Productassetclasses | 0 | 1.14 KB |
| aims_productcharacteristics.parquet | Productcharacteristics | 0 | 1.98 KB |
| aims_productlinks.parquet | Productlinks | 0 | 951.00 B |
| aims_products.parquet | Products | 0 | 2.11 KB |
| aims_projectitemactions.parquet | Projectitemactions | 5 | 9.31 KB |
| aims_projectitemassignedroles.parquet | Projectitemassignedroles | 1 | 2.33 KB |
| aims_projectitemattributes.parquet | Projectitemattributes | 3 | 8.89 KB |
| aims_projectitemlinks.parquet | Projectitemlinks | 0 | 1.22 KB |
| aims_projectitems.parquet | Projectitems | 1 | 3.57 KB |
| aims_taskdefinitions.parquet | Taskdefinitions | 5 | 5.62 KB |
| aims_ua_beneficiaries.parquet | Ua_Beneficiaries | 8305 | 144.28 KB |
| aims_ua_comments.parquet | Ua_Comments | 59 | 18.68 KB |
| aims_ua_entities.parquet | Ua_Entities | 832 | 24.26 KB |
| aims_ua_meetingattendees.parquet | Ua_Meetingattendees | 180 | 6.44 KB |
| aims_ua_meetings.parquet | Ua_Meetings | 81 | 4.84 KB |
| aims_ua_noncompimppartytypes.parquet | Ua_Noncompimppartytypes | 40 | 3.76 KB |
| aims_ua_noncomplianceimpacts.parquet | Ua_Noncomplianceimpacts | 171 | 6.31 KB |
| aims_ua_noncompotheruas.parquet | Ua_Noncompotheruas | 15 | 6.27 KB |
| aims_ua_optionvalues.parquet | Ua_Optionvalues | 110 | 4.11 KB |
| aims_undertakings_assurances.parquet | Undertakings_Assurances | 4952 | 1.92 MB |
| aims_workbanks.parquet | Workbanks | 0 | 1.74 KB |
| aims_workbankworkorders.parquet | Workbankworkorders | 0 | 1.05 KB |
| aims_workorderattributes.parquet | Workorderattributes | 0 | 1.79 KB |
| aims_workorders.parquet | Workorders | 0 | 2.29 KB |
| aims_workorderstatustransition.parquet | Workorderstatustransition | 0 | 1.83 KB |