"""Unit tests for KG triple extraction: parse_dotnet_project_file, parse_sln_file,
and parse_xaml_file in miner.py.

Covers:
- .csproj/.fsproj/.vbproj: TargetFramework, OutputType, PackageReference, ProjectReference
- .sln: project list parsing and SolutionFolder filtering
- .xaml: x:Class, code-behind, DataContext, x:Name, resources, commands
- Edge cases: empty files, malformed XML, no references
- KG lifecycle: re-mining invalidates stale triples
"""

from pathlib import Path

from mempalace.miner import parse_dotnet_project_file, parse_sln_file, parse_xaml_file


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


# =============================================================================
# XAML fixtures
# =============================================================================

# Full WPF-style XAML exercising: x:Class, d:DataContext, x:Name,
# StaticResource, DynamicResource, and Command binding.
_XAML_FULL = """\
<Window x:Class="MyApp.MainWindow"
        xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        xmlns:d="http://schemas.microsoft.com/expression/blend/2008"
        xmlns:local="clr-namespace:MyApp.ViewModels"
        d:DataContext="{d:DesignInstance Type=local:MainViewModel}">
    <Grid>
        <TextBox x:Name="txtUsername" Style="{StaticResource InputStyle}" />
        <Button Content="Save" Command="{Binding SaveCommand}"
                Background="{DynamicResource ThemeBrush}" />
    </Grid>
</Window>
"""

# Resource dictionary — no x:Class, no code-behind
_XAML_RESOURCE_DICT = """\
<ResourceDictionary
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">
    <Style x:Key="InputStyle" TargetType="TextBox">
        <Setter Property="Margin" Value="5" />
    </Style>
    <SolidColorBrush x:Key="ThemeBrush" Color="#336699" />
</ResourceDictionary>
"""

# DataContext via element syntax (not d:DataContext attribute)
_XAML_ELEMENT_DATACONTEXT = """\
<Window x:Class="MyApp.DetailView"
        xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        xmlns:local="clr-namespace:MyApp.ViewModels">
    <Window.DataContext>
        <local:DetailViewModel />
    </Window.DataContext>
    <Grid />
</Window>
"""


# =============================================================================
# parse_xaml_file — x:Class and view name extraction
# =============================================================================


def test_parse_xaml_xclass_view_name(tmp_path):
    """x:Class='MyApp.MainWindow' → subject 'MainWindow'."""
    f = tmp_path / "MainWindow.xaml"
    f.write_text(_XAML_FULL, encoding="utf-8")
    triples = triples_as_set(parse_xaml_file(f))
    # At least one triple must have subject 'MainWindow'
    assert any(t[0] == "MainWindow" for t in triples)


def test_parse_xaml_no_xclass_uses_filename_stem(tmp_path):
    """No x:Class → view name falls back to filename stem."""
    f = tmp_path / "Styles.xaml"
    f.write_text(_XAML_RESOURCE_DICT, encoding="utf-8")
    triples = parse_xaml_file(f)
    # Triples may be empty (no named controls, resources, etc. from this file)
    # but if any triples are emitted, subject must be "Styles"
    assert all(t[0] == "Styles" for t in triples)


# =============================================================================
# parse_xaml_file — code-behind link (AC-2)
# =============================================================================


def test_parse_xaml_code_behind_emitted_when_file_exists(tmp_path):
    """has_code_behind triple emitted only when .xaml.cs adjacent file exists."""
    f = tmp_path / "MainWindow.xaml"
    f.write_text(_XAML_FULL, encoding="utf-8")
    code_behind = tmp_path / "MainWindow.xaml.cs"
    code_behind.write_text("// code behind\n", encoding="utf-8")

    triples = triples_as_set(parse_xaml_file(f))
    assert ("MainWindow", "has_code_behind", "MainWindow.xaml.cs") in triples


def test_parse_xaml_code_behind_not_emitted_when_missing(tmp_path):
    """has_code_behind triple NOT emitted when no .xaml.cs adjacent file exists."""
    f = tmp_path / "MainWindow.xaml"
    f.write_text(_XAML_FULL, encoding="utf-8")
    # No .xaml.cs created

    triples = triples_as_set(parse_xaml_file(f))
    assert not any(t[1] == "has_code_behind" for t in triples)


# =============================================================================
# parse_xaml_file — DataContext bindings (AC-3, AC-4)
# =============================================================================


def test_parse_xaml_element_datacontext(tmp_path):
    """Element-style DataContext emits binds_viewmodel triple."""
    f = tmp_path / "DetailView.xaml"
    f.write_text(_XAML_ELEMENT_DATACONTEXT, encoding="utf-8")
    triples = triples_as_set(parse_xaml_file(f))
    assert ("DetailView", "binds_viewmodel", "DetailViewModel") in triples


def test_parse_xaml_design_instance_datacontext(tmp_path):
    """d:DataContext='{d:DesignInstance Type=vm:MainViewModel}' emits binds_viewmodel."""
    f = tmp_path / "MainWindow.xaml"
    f.write_text(_XAML_FULL, encoding="utf-8")
    triples = triples_as_set(parse_xaml_file(f))
    assert ("MainWindow", "binds_viewmodel", "MainViewModel") in triples


def test_parse_xaml_design_instance_no_type_prefix(tmp_path):
    """d:DataContext='{d:DesignInstance MyViewModel}' (no Type= prefix) still extracts VM."""
    content = """\
<Window x:Class="App.MyView"
        xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        xmlns:d="http://schemas.microsoft.com/expression/blend/2008"
        d:DataContext="{d:DesignInstance MyViewModel}">
    <Grid />
</Window>
"""
    f = tmp_path / "MyView.xaml"
    f.write_text(content, encoding="utf-8")
    triples = triples_as_set(parse_xaml_file(f))
    assert ("MyView", "binds_viewmodel", "MyViewModel") in triples


# =============================================================================
# parse_xaml_file — named controls (AC-5)
# =============================================================================


def test_parse_xaml_named_control(tmp_path):
    """x:Name='txtUsername' emits has_named_control triple."""
    f = tmp_path / "MainWindow.xaml"
    f.write_text(_XAML_FULL, encoding="utf-8")
    triples = triples_as_set(parse_xaml_file(f))
    assert ("MainWindow", "has_named_control", "txtUsername") in triples


# =============================================================================
# parse_xaml_file — resource references (AC-6, AC-7)
# =============================================================================


def test_parse_xaml_static_resource(tmp_path):
    """StaticResource reference emits references_resource triple."""
    f = tmp_path / "MainWindow.xaml"
    f.write_text(_XAML_FULL, encoding="utf-8")
    triples = triples_as_set(parse_xaml_file(f))
    assert ("MainWindow", "references_resource", "InputStyle") in triples


def test_parse_xaml_dynamic_resource(tmp_path):
    """DynamicResource reference emits references_resource triple."""
    f = tmp_path / "MainWindow.xaml"
    f.write_text(_XAML_FULL, encoding="utf-8")
    triples = triples_as_set(parse_xaml_file(f))
    assert ("MainWindow", "references_resource", "ThemeBrush") in triples


def test_parse_xaml_resource_references_deduplicated(tmp_path):
    """Same resource key referenced multiple times produces only one triple."""
    content = """\
<Window x:Class="App.RepeatView"
        xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">
    <StackPanel>
        <TextBox Style="{StaticResource InputStyle}" />
        <Button Style="{StaticResource InputStyle}" />
    </StackPanel>
</Window>
"""
    f = tmp_path / "RepeatView.xaml"
    f.write_text(content, encoding="utf-8")
    triples = parse_xaml_file(f)
    resource_triples = [
        t for t in triples if t[1] == "references_resource" and t[2] == "InputStyle"
    ]
    assert len(resource_triples) == 1


# =============================================================================
# parse_xaml_file — command bindings (AC-8)
# =============================================================================


def test_parse_xaml_command_binding(tmp_path):
    """Command='{Binding SaveCommand}' emits uses_command triple."""
    f = tmp_path / "MainWindow.xaml"
    f.write_text(_XAML_FULL, encoding="utf-8")
    triples = triples_as_set(parse_xaml_file(f))
    assert ("MainWindow", "uses_command", "SaveCommand") in triples


def test_parse_xaml_command_binding_path_form(tmp_path):
    """Command='{Binding Path=DeleteCommand}' also emits uses_command triple."""
    content = """\
<Window x:Class="App.EditView"
        xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">
    <Button Command="{Binding Path=DeleteCommand}" />
</Window>
"""
    f = tmp_path / "EditView.xaml"
    f.write_text(content, encoding="utf-8")
    triples = triples_as_set(parse_xaml_file(f))
    assert ("EditView", "uses_command", "DeleteCommand") in triples


# =============================================================================
# parse_xaml_file — edge cases (AC-9)
# =============================================================================


def test_parse_xaml_empty_file(tmp_path):
    """Empty file returns empty triple list without exception."""
    f = tmp_path / "Empty.xaml"
    f.write_text("", encoding="utf-8")
    assert parse_xaml_file(f) == []


def test_parse_xaml_malformed_xml(tmp_path):
    """Malformed XML returns empty triple list without exception."""
    f = tmp_path / "Broken.xaml"
    f.write_text("<Window x:Class='App.Foo'><Unclosed>", encoding="utf-8")
    assert parse_xaml_file(f) == []


def test_parse_xaml_resource_dict_no_xclass(tmp_path):
    """Resource dictionary (no x:Class) uses filename stem; no spurious triples."""
    f = tmp_path / "CommonStyles.xaml"
    f.write_text(_XAML_RESOURCE_DICT, encoding="utf-8")
    triples = parse_xaml_file(f)
    # Subject must be "CommonStyles" (filename stem), not something parsed from XML
    assert all(t[0] == "CommonStyles" for t in triples)
    # No code-behind, no named controls, no viewmodel triples expected
    assert not any(t[1] == "has_code_behind" for t in triples)
    assert not any(t[1] == "binds_viewmodel" for t in triples)


# =============================================================================
# KG lifecycle — re-mining a changed .xaml invalidates stale triples (AC-10)
# =============================================================================


def test_xaml_remining_invalidates_stale_triples(tmp_path):
    """After changing a .xaml and re-mining, old KG triples are invalidated."""
    import yaml
    from mempalace.knowledge_graph import KnowledgeGraph
    from mempalace.miner import mine

    project_root = tmp_path / "project"
    project_root.mkdir()

    # Initial XAML with one named control and one resource
    xaml_file = project_root / "MainWindow.xaml"
    xaml_file.write_text(
        '<Window x:Class="MyApp.MainWindow"\n'
        '        xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"\n'
        '        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">\n'
        '    <TextBox x:Name="oldControl" Style="{StaticResource OldStyle}" />\n'
        "</Window>\n",
        encoding="utf-8",
    )
    (project_root / "mempalace.yaml").write_text(
        yaml.dump(
            {"wing": "test_xaml_lifecycle", "rooms": [{"name": "general", "description": "All"}]}
        ),
        encoding="utf-8",
    )

    palace_path = str(tmp_path / "palace")
    kg = KnowledgeGraph(db_path=str(tmp_path / "kg.sqlite3"))

    # First mine
    mine(str(project_root), palace_path, kg=kg, incremental=False)

    first_triples = kg.query_entity("MainWindow")
    control_objs = {t["object"] for t in first_triples if t["predicate"] == "has_named_control"}
    assert "oldControl" in control_objs, f"Expected oldControl after first mine, got {control_objs}"

    # Update XAML — replace named control
    xaml_file.write_text(
        '<Window x:Class="MyApp.MainWindow"\n'
        '        xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"\n'
        '        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">\n'
        '    <TextBox x:Name="newControl" Style="{StaticResource NewStyle}" />\n'
        "</Window>\n",
        encoding="utf-8",
    )

    # Second mine — stale triples invalidated
    mine(str(project_root), palace_path, kg=kg, incremental=False)

    second_triples = kg.query_entity("MainWindow")
    current_controls = {
        t["object"]
        for t in second_triples
        if t["predicate"] == "has_named_control" and t["current"]
    }
    assert "newControl" in current_controls, (
        f"Expected newControl as current, got {current_controls}"
    )
    assert "oldControl" not in current_controls, (
        f"oldControl should be invalidated, but is still current: {current_controls}"
    )
