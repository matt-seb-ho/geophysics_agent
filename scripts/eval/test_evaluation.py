#!/usr/bin/env python3
"""
Quick test to verify the LLM evaluation pipeline works.

Creates minimal XML files and tests the evaluation flow.

Usage:
    uv run python scripts/eval/test_evaluation.py
"""

import tempfile
from pathlib import Path
import sys

# Import from llm_judge_xml
sys.path.insert(0, str(Path(__file__).parent))
from llm_judge_xml import judge_xml_with_llm, print_evaluation_report


# Sample XML files for testing
GROUND_TRUTH_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Problem>
  <Solvers>
    <SolidMechanicsLagrangianFEM name="mechanicsSolver"
                                   discretization="FE1"
                                   targetRegions="cb1">
      <QuasiStatic/>
    </SolidMechanicsLagrangianFEM>
  </Solvers>

  <Mesh>
    <InternalWellbore name="mesh1"
                      radius="0.1"
                      theta="360"
                      nr="10"
                      nt="20"
                      nz="5">
      <Trajectory>
        <Point coords="0.0, 0.0, 0.0"/>
        <Point coords="0.0, 0.0, 2.0"/>
      </Trajectory>
    </InternalWellbore>
  </Mesh>

  <Constitutive>
    <ExtendedDruckerPrager name="rock"
                           defaultDensity="2500"
                           defaultBulkModulus="500e6"
                           defaultShearModulus="300e6"
                           defaultCohesion="0.0"
                           defaultInitialFrictionAngle="15.27"/>
  </Constitutive>
</Problem>
"""

GENERATED_XML_GOOD = """<?xml version="1.0" encoding="UTF-8"?>
<Problem>
  <Solvers>
    <SolidMechanicsLagrangianFEM name="mechanicsSolver"
                                   discretization="FE1"
                                   targetRegions="cb1">
      <QuasiStatic/>
    </SolidMechanicsLagrangianFEM>
  </Solvers>

  <Mesh>
    <InternalWellbore name="mesh1"
                      radius="0.1"
                      theta="360"
                      nr="10"
                      nt="20"
                      nz="5">
      <Trajectory>
        <Point coords="0.0, 0.0, 0.0"/>
        <Point coords="0.0, 0.0, 2.0"/>
      </Trajectory>
    </InternalWellbore>
  </Mesh>

  <Constitutive>
    <ExtendedDruckerPrager name="rock"
                           defaultDensity="2500.0"
                           defaultBulkModulus="5e8"
                           defaultShearModulus="3e8"
                           defaultCohesion="0.0"
                           defaultInitialFrictionAngle="15.27"/>
  </Constitutive>
</Problem>
"""

GENERATED_XML_POOR = """<?xml version="1.0" encoding="UTF-8"?>
<Problem>
  <Solvers>
    <SolidMechanicsLagrangianFEM name="mechanicsSolver"
                                   discretization="FE1"
                                   targetRegions="cb1">
    </SolidMechanicsLagrangianFEM>
  </Solvers>

  <Mesh>
    <InternalWellbore name="mesh1"
                      radius="0.1"
                      theta="180"
                      nr="5"
                      nt="10"
                      nz="2">
      <Trajectory>
        <Point coords="0.0, 0.0, 0.0"/>
        <Point coords="0.0, 0.0, 1.0"/>
      </Trajectory>
    </InternalWellbore>
  </Mesh>

  <Constitutive>
    <ElasticIsotropic name="rock"
                      defaultDensity="2000"
                      defaultBulkModulus="400e6"
                      defaultShearModulus="250e6"/>
  </Constitutive>
</Problem>
"""


def test_good_xml():
    """Test evaluation with high-quality generated XML."""
    print("\n" + "="*80)
    print("TEST 1: Evaluating GOOD generated XML")
    print("="*80)

    try:
        evaluation = judge_xml_with_llm(
            GROUND_TRUTH_XML,
            GENERATED_XML_GOOD,
            model="anthropic/claude-3.5-sonnet"
        )

        print_evaluation_report(evaluation, verbose=True)

        # Check if score is reasonable
        if evaluation["overall_score"] < 7.0:
            print("\n⚠️  WARNING: Expected high score (>7.0) but got {:.1f}/10".format(
                evaluation["overall_score"]
            ))
            return False
        else:
            print("\n✓ Test passed: Good XML scored {:.1f}/10".format(
                evaluation["overall_score"]
            ))
            return True

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        return False


def test_poor_xml():
    """Test evaluation with poor-quality generated XML."""
    print("\n" + "="*80)
    print("TEST 2: Evaluating POOR generated XML")
    print("="*80)

    try:
        evaluation = judge_xml_with_llm(
            GROUND_TRUTH_XML,
            GENERATED_XML_POOR,
            model="anthropic/claude-3.5-sonnet"
        )

        print_evaluation_report(evaluation, verbose=True)

        # Check if score is reasonable
        if evaluation["overall_score"] > 8.0:
            print("\n⚠️  WARNING: Expected low score (<8.0) but got {:.1f}/10".format(
                evaluation["overall_score"]
            ))
            return False
        else:
            print("\n✓ Test passed: Poor XML scored {:.1f}/10".format(
                evaluation["overall_score"]
            ))
            return True

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        return False


def main():
    print("\n" + "="*80)
    print("LLM EVALUATION PIPELINE - QUICK TEST")
    print("="*80)
    print("\nThis test verifies that the LLM judge can:")
    print("  1. Evaluate high-quality XML (should score >7.0)")
    print("  2. Detect issues in poor-quality XML (should score <8.0)")
    print("\nNote: This requires OPENROUTER_API_KEY to be set in .env")

    # Run tests
    results = []

    print("\n" + "-"*80)
    results.append(("Good XML", test_good_xml()))

    print("\n" + "-"*80)
    results.append(("Poor XML", test_poor_xml()))

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")
    print("="*80 + "\n")

    # Exit with error if any test failed
    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    main()
