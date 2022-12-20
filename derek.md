Hosts:
  - Unique Key: Name
  - Unique Key: IP Addr
  - Meta_Info
  - 0 or more Batches

Groups:
  - Unique Key: Name
  - Meta_Info
  - 0 or more Hosts

Batches:
  - Unique Key: Name
  - Meta_Info
  - Priority (integer)
  - ttl (integer)
  - 0 or more Archivers
  - 1 or more Schedules
  - 1 BSSID Scan
  - 1 or more SSID Profiles
  - 1 or more Jobs. (This is ordinal, they need to be in explicit order: Job 1, Job 2, etc.)

Archivers:
  - Unique Key: Name
  - Meta_Info
  - 1 Archiver Type @ corresponding archiver_spec

Tests:
  - Unique Key: Name
  - Meta_Info
  - 1 Archiver Type @ corresponding test_spec

Test_spec:
  - Unique Key: Name
  - parameters

Archiver_spec:
  - Uniquekey: Name
  - parameters

Job:
  - Unique Key: Name
  - Meta_Info
  - 1 or more tests
  - Continue-If

Schedules:
  - Unique Key: name
  - meta_info
  - cron_syntax


BSSID Scans:
SSID Profiles:
Tests:
Jobs:

Jobs:
