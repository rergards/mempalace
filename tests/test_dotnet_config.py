"""Unit tests for parse_dotnet_project_file() and parse_sln_file() in miner.py.

Covers:
- Basic XML extraction (TargetFramework, OutputType, PackageReference, ProjectReference)
- MSBuild namespace-prefixed XML
- .sln project list parsing and SolutionFolder filtering
- Edge cases: empty files, malformed XML, no references
- KG lifecycle: re-mining a changed .csproj invalidates stale triples before adding new ones
"""

from pathlib import Path

from mempalace.miner import parse_dotnet_project_file, parse_sln_file


# =============================================================================
# Helpers
# =============================================================================


def write_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def triples_as_set(triples: list) -> set:
    return set(tuple(t) for t in triples)


# =============================================================================
# parse_dotnet_project_file — basic extraction
# =============================================================================

_CSPROJ_BASIC = """\
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <OutputType>Exe</OutputType>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Newtonsoft.Json" Version="13.0.3" />
    <PackageReference Include="Serilog" Version="3.1.1" />
    <ProjectReference Include="../Shared/Shared.csproj" />
  </ItemGroup>
</Project>
"""


def test_parse_csproj_target_framework(tmp_path):
    f = tmp_path / "MyApp.csproj"
    f.write_text(_CSPROJ_BASIC, encoding="utf-8")
    triples = triples_as_set(parse_dotnet_project_file(f))
    assert ("MyApp", "targets_framework", "net8.0") in triples


def test_parse_csproj_output_type(tmp_path):
    f = tmp_path / "MyApp.csproj"
    f.write_text(_CSPROJ_BASIC, encoding="utf-8")
    triples = triples_as_set(parse_dotnet_project_file(f))
    assert ("MyApp", "has_output_type", "Exe") in triples


def test_parse_csproj_package_references(tmp_path):
    f = tmp_path / "MyApp.csproj"
    f.write_text(_CSPROJ_BASIC, encoding="utf-8")
    triples = triples_as_set(parse_dotnet_project_file(f))
    assert ("MyApp", "depends_on", "Newtonsoft.Json@13.0.3") in triples
    assert ("MyApp", "depends_on", "Serilog@3.1.1") in triples


def test_parse_csproj_project_reference(tmp_path):
    f = tmp_path / "MyApp.csproj"
    f.write_text(_CSPROJ_BASIC, encoding="utf-8")
    triples = triples_as_set(parse_dotnet_project_file(f))
    # Stem of "../Shared/Shared.csproj" is "Shared"
    assert ("MyApp", "references_project", "Shared") in triples


def test_parse_csproj_project_name_from_stem(tmp_path):
    """Project name is derived from the filename stem, not the XML content."""
    f = tmp_path / "WeirdName.csproj"
    f.write_text(_CSPROJ_BASIC, encoding="utf-8")
    triples = triples_as_set(parse_dotnet_project_file(f))
    assert ("WeirdName", "targets_framework", "net8.0") in triples
    # The name from _CSPROJ_BASIC ("MyApp") must NOT appear as subject
    assert not any(t[0] == "MyApp" for t in triples)


# =============================================================================
# parse_dotnet_project_file — TargetFrameworks (plural, multi-target)
# =============================================================================

_CSPROJ_MULTI_TARGET = """\
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFrameworks>net8.0;net6.0;netstandard2.0</TargetFrameworks>
    <OutputType>Library</OutputType>
  </PropertyGroup>
</Project>
"""


def test_parse_csproj_multi_target_frameworks(tmp_path):
    """TargetFrameworks (plural) with semicolon-delimited values emits one triple per target."""
    f = tmp_path / "MyLib.csproj"
    f.write_text(_CSPROJ_MULTI_TARGET, encoding="utf-8")
    triples = triples_as_set(parse_dotnet_project_file(f))
    assert ("MyLib", "targets_framework", "net8.0") in triples
    assert ("MyLib", "targets_framework", "net6.0") in triples
    assert ("MyLib", "targets_framework", "netstandard2.0") in triples


def test_parse_csproj_multi_target_no_singular_duplicate(tmp_path):
    """A project with only TargetFrameworks (plural) does NOT emit TargetFramework (singular)."""
    f = tmp_path / "MyLib.csproj"
    f.write_text(_CSPROJ_MULTI_TARGET, encoding="utf-8")
    triples = parse_dotnet_project_file(f)
    # Three separate triples, all with predicate "targets_framework"
    fw_triples = [t for t in triples if t[1] == "targets_framework"]
    assert len(fw_triples) == 3


# =============================================================================
# parse_dotnet_project_file — MSBuild namespace-prefixed XML
# =============================================================================

_CSPROJ_NS = """\
<Project xmlns="http://schemas.microsoft.com/developer/msbuild/2003">
  <PropertyGroup>
    <TargetFramework>net6.0</TargetFramework>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="AutoMapper" Version="12.0.1" />
  </ItemGroup>
</Project>
"""


def test_parse_csproj_msbuild_namespace(tmp_path):
    """Namespace-prefixed MSBuild XML must be parsed without errors."""
    f = tmp_path / "LegacyApp.csproj"
    f.write_text(_CSPROJ_NS, encoding="utf-8")
    triples = triples_as_set(parse_dotnet_project_file(f))
    assert ("LegacyApp", "targets_framework", "net6.0") in triples
    assert ("LegacyApp", "depends_on", "AutoMapper@12.0.1") in triples


# =============================================================================
# parse_dotnet_project_file — edge cases
# =============================================================================


def test_parse_csproj_empty_file(tmp_path):
    """Empty file returns an empty triple list (no exception)."""
    f = tmp_path / "Empty.csproj"
    f.write_text("", encoding="utf-8")
    assert parse_dotnet_project_file(f) == []


def test_parse_csproj_malformed_xml(tmp_path):
    """Malformed XML returns an empty triple list (no exception)."""
    f = tmp_path / "Broken.csproj"
    f.write_text("<Project><Unclosed>", encoding="utf-8")
    assert parse_dotnet_project_file(f) == []


def test_parse_csproj_no_references(tmp_path):
    """A project with no references produces only framework/output triples."""
    content = (
        '<Project Sdk="Microsoft.NET.Sdk">\n'
        "  <PropertyGroup>\n"
        "    <TargetFramework>net8.0</TargetFramework>\n"
        "  </PropertyGroup>\n"
        "</Project>\n"
    )
    f = tmp_path / "Minimal.csproj"
    f.write_text(content, encoding="utf-8")
    triples = parse_dotnet_project_file(f)
    assert ("Minimal", "targets_framework", "net8.0") in triples
    assert not any(t[1] == "depends_on" for t in triples)
    assert not any(t[1] == "references_project" for t in triples)


def test_parse_csproj_package_ref_no_version(tmp_path):
    """PackageReference without Version attribute uses bare name (no @ suffix)."""
    content = (
        '<Project Sdk="Microsoft.NET.Sdk">\n'
        "  <ItemGroup>\n"
        '    <PackageReference Include="SomePackage" />\n'
        "  </ItemGroup>\n"
        "</Project>\n"
    )
    f = tmp_path / "App.csproj"
    f.write_text(content, encoding="utf-8")
    triples = triples_as_set(parse_dotnet_project_file(f))
    assert ("App", "depends_on", "SomePackage") in triples


def test_parse_csproj_windows_path_separator(tmp_path):
    """ProjectReference paths with backslashes yield the correct stem."""
    content = (
        '<Project Sdk="Microsoft.NET.Sdk">\n'
        "  <ItemGroup>\n"
        '    <ProjectReference Include="..\\\\Domain\\\\Domain.csproj" />\n'
        "  </ItemGroup>\n"
        "</Project>\n"
    )
    f = tmp_path / "Api.csproj"
    f.write_text(content, encoding="utf-8")
    triples = triples_as_set(parse_dotnet_project_file(f))
    assert ("Api", "references_project", "Domain") in triples


# =============================================================================
# parse_sln_file — basic extraction
# =============================================================================

_SLN_BASIC = """\

Microsoft Visual Studio Solution File, Format Version 12.00
# Visual Studio Version 17
VisualStudioVersion = 17.0.31903.59
MinimumVisualStudioVersion = 10.0.40219.1
Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "MyApp", "MyApp\\MyApp.csproj", "{11111111-1111-1111-1111-111111111111}"
EndProject
Project("{F2A71F9B-5D33-465A-A702-920D77279786}") = "MyLib", "MyLib\\MyLib.fsproj", "{22222222-2222-2222-2222-222222222222}"
EndProject
Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "Domain", "Domain\\Domain.vbproj", "{33333333-3333-3333-3333-333333333333}"
EndProject
Global
EndGlobal
"""


def test_parse_sln_contains_project_triples(tmp_path):
    f = tmp_path / "MySolution.sln"
    f.write_text(_SLN_BASIC, encoding="utf-8")
    triples = triples_as_set(parse_sln_file(f))
    assert ("MySolution", "contains_project", "MyApp") in triples
    assert ("MySolution", "contains_project", "MyLib") in triples
    assert ("MySolution", "contains_project", "Domain") in triples


def test_parse_sln_solution_name_from_stem(tmp_path):
    f = tmp_path / "BigSolution.sln"
    f.write_text(_SLN_BASIC, encoding="utf-8")
    triples = parse_sln_file(f)
    subjects = {t[0] for t in triples}
    assert "BigSolution" in subjects
    # Original solution name from _SLN_BASIC ("MySolution") must not appear
    assert "MySolution" not in subjects


# =============================================================================
# parse_sln_file — SolutionFolder filtering
# =============================================================================

_SLN_WITH_FOLDER = """\

Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "MyApp", "MyApp\\MyApp.csproj", "{AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA}"
EndProject
Project("{2150E333-8FDC-42A3-9474-1A3956D46DE8}") = "src", "src", "{BBBBBBBB-BBBB-BBBB-BBBB-BBBBBBBBBBBB}"
EndProject
"""


def test_parse_sln_solution_folder_excluded(tmp_path):
    """SolutionFolder entries (no .csproj/.fsproj/.vbproj extension) must not emit triples."""
    f = tmp_path / "Filtered.sln"
    f.write_text(_SLN_WITH_FOLDER, encoding="utf-8")
    triples = triples_as_set(parse_sln_file(f))
    # Only the real project should appear
    assert ("Filtered", "contains_project", "MyApp") in triples
    # The "src" SolutionFolder must NOT appear
    assert not any(t[2] == "src" for t in triples)


# =============================================================================
# parse_sln_file — edge cases
# =============================================================================


def test_parse_sln_empty_file(tmp_path):
    f = tmp_path / "Empty.sln"
    f.write_text("", encoding="utf-8")
    assert parse_sln_file(f) == []


def test_parse_sln_no_projects(tmp_path):
    content = "\nMicrosoft Visual Studio Solution File, Format Version 12.00\nGlobal\nEndGlobal\n"
    f = tmp_path / "Empty.sln"
    f.write_text(content, encoding="utf-8")
    assert parse_sln_file(f) == []


# =============================================================================
# KG lifecycle — re-mining a changed .csproj invalidates stale triples
# =============================================================================


def test_csproj_remining_invalidates_stale_triples(tmp_path):
    """After changing a .csproj and re-mining, old KG triples are invalidated."""
    import yaml
    from mempalace.knowledge_graph import KnowledgeGraph
    from mempalace.miner import mine

    project_root = tmp_path / "project"
    project_root.mkdir()

    # Write initial .csproj with one dependency
    csproj = project_root / "Api.csproj"
    csproj.write_text(
        '<Project Sdk="Microsoft.NET.Sdk">\n'
        "  <ItemGroup>\n"
        '    <PackageReference Include="OldDep" Version="1.0.0" />\n'
        "  </ItemGroup>\n"
        "</Project>\n",
        encoding="utf-8",
    )
    (project_root / "mempalace.yaml").write_text(
        yaml.dump(
            {"wing": "test_kg_lifecycle", "rooms": [{"name": "general", "description": "All"}]}
        ),
        encoding="utf-8",
    )

    palace_path = str(tmp_path / "palace")
    kg = KnowledgeGraph(db_path=str(tmp_path / "kg.sqlite3"))

    # First mine — adds triple (Api, depends_on, OldDep@1.0.0)
    mine(str(project_root), palace_path, kg=kg, incremental=False)

    triples_after_first = kg.query_entity("Api")
    dep_objs = {t["object"] for t in triples_after_first if t["predicate"] == "depends_on"}
    assert "OldDep@1.0.0" in dep_objs, f"Expected OldDep@1.0.0 after first mine, got {dep_objs}"

    # Update .csproj — replace with a new dependency
    csproj.write_text(
        '<Project Sdk="Microsoft.NET.Sdk">\n'
        "  <ItemGroup>\n"
        '    <PackageReference Include="NewDep" Version="2.0.0" />\n'
        "  </ItemGroup>\n"
        "</Project>\n",
        encoding="utf-8",
    )

    # Second mine — should invalidate OldDep@1.0.0 and add NewDep@2.0.0
    mine(str(project_root), palace_path, kg=kg, incremental=False)

    triples_after_second = kg.query_entity("Api")
    current_dep_objs = {
        t["object"] for t in triples_after_second if t["predicate"] == "depends_on" and t["current"]
    }
    assert "NewDep@2.0.0" in current_dep_objs, (
        f"Expected NewDep@2.0.0 as current triple, got {current_dep_objs}"
    )
    assert "OldDep@1.0.0" not in current_dep_objs, (
        f"OldDep@1.0.0 should be invalidated, but is still current: {current_dep_objs}"
    )
