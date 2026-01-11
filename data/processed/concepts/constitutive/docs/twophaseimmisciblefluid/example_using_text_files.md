**Context:** Constitutive > TwoPhaseImmiscibleFluid > Example using text files

# Example using text files
``xml
  <Constitutive>
    <TwoPhaseImmiscibleFluid
      name="fluid"
      phaseNames="{ oil, water }"
      tableNames="{ oil.txt, water.txt }" />
  </Constitutive>


with, for example, `water.txt` being set as:

```text
  #  P(Pa) Dens(kg/m3) Visc(Pa.s)
   2068000     980.683     0.0003     
   5516000      982.07     0.0003
  30600000     992.233     0.0003
  55160000    1002.265     0.0003
