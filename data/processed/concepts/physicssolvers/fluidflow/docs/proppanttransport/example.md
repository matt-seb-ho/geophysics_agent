**Context:** Physicssolvers > Fluidflow > ProppantTransport > Example

# Example
First, we specify the proppant transport solver itself and apply it to the fracture region:


  :language: xml
  :start-after: <!-- SPHINX_PROPPANT_TRANSPORT_SOLVER_BEGIN -->
  :end-before: <!-- SPHINX_PROPPANT_TRANSPORT_SOLVER_END -->

Then, we specify a compatible flow solver (currently a specialized `SinglePhaseProppantFVM` solver must be used):


  :language: xml
  :start-after: <!-- SPHINX_PROPPANT_FLOW_SOLVER_BEGIN -->
  :end-before: <!-- SPHINX_PROPPANT_FLOW_SOLVER_END -->

Finally, we couple them through a coupled solver that references the two above:


  :language: xml
  :start-after: <!-- SPHINX_PROPPANT_COUPLED_SOLVER_BEGIN -->
  :end-before: <!-- SPHINX_PROPPANT_COUPLED_SOLVER_END -->
