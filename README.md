# Hadar
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/hadar-solver/hadar?sort=semver)
![GitHub Workflow Status (branch)](https://img.shields.io/github/workflow/status/hadar-solver/hadar/main/master)
![https://sonarcloud.io/dashboard?id=hadar-solver_hadar](https://sonarcloud.io/api/project_badges/measure?project=hadar-solver_hadar&metric=alert_status)
![https://sonarcloud.io/dashboard?id=hadar-solver_hadar](https://sonarcloud.io/api/project_badges/measure?project=hadar-solver_hadar&metric=coverage)
![GitHub](https://img.shields.io/github/license/hadar-solver/hadar)


Hadar is a adequacy python library for deterministic and stochastic computation

## Adequacy problem

Each kind of network has a needs of adequacy. On one side, some network nodes need to consume
items such as watt, litter, package. And other side, some network nodes produce items.
Applying adequacy on network, is tring to find the best available exchanges to avoid any lack at the best cost.

For example, a electric grid can have some nodes wich produce too more power and some nodes wich produce not enough power.

![mermaid](https://mermaidjs.github.io/mermaid-live-editor/#/view/eyJjb2RlIjoiZ3JhcGggTFJcbiAgICBBKEEgPGJyLz5sb2FkPTIwPGJyLz5wcm9kPTMwKSAtLS0gQihCPGJyLz5sb2FkPTIwPGJyLz5wcm9kPTEwKSIsIm1lcm1haWQiOnsidGhlbWUiOiJkZWZhdWx0In19)

In this case, A produce 10 more and B need 10 more. Perform adequecy is quiet easy : A will share 10 to B

![mermaid](https://mermaidjs.github.io/mermaid-live-editor/#/view/eyJjb2RlIjoiZ3JhcGggTFJcbiAgICBBKEEgPGJyLz5sb2FkPTIwPGJyLz5wcm9kPTMwKSAtLSBzaGFyZSAxMCAtLT4gQihCPGJyLz5sb2FkPTIwPGJyLz5wcm9kPTEwKSIsIm1lcm1haWQiOnsidGhlbWUiOiJkZWZhdWx0In19)
