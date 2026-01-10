**Context:** Physicssolvers > Fluidflow > ProppantTransport > Theory

# Theory
The following mass balance and constitutive equations are solved inside fractures,

### Proppant-fluid Slurry Flow


where the proppant-fluid mixture velocity :math:`\boldsymbol{u_m}` is approximated by the Darcy's law as,



and :math:`p` is pressure, :math:`\rho_m` and :math:`\mu_m` are density and viscosity of the mixed fluid , respectively,  and :math:`\boldsymbol{g}` is the gravity vector. The fracture permeability :math:`K_f` is determined based on fracture aperture :math:`a` as




### Proppant Transport


in which :math:`c` and :math:`\boldsymbol{u}_p` represent the volume fraction and velocity of the proppant particles.


### Multi-component Fluid Transport


Here :math:`\boldsymbol{u}_f` represents the carrying fluid velocity. :math:`\rho_i` and :math:`\omega_i` denote the density and concentration of `i-th` component in fluid, respectively. The fluid density :math:`\rho_f` can now be readily written as



where :math:`N_c` is the number of components in fluid.
Similarly, the fluid viscosity :math:`\mu_f` can be calculated by the mass fraction weighted average of the component viscosities.

The density and velocity of the slurry fluid are further expressed as,



and



in which :math:`\rho_f` and :math:`\boldsymbol{u}_f` are the density and velocity of the carrying fluid, and :math:`\rho_p` is the density of the proppant particles.


### Proppant Slip Velocity
The proppant particle and carrying fluid velocities are related by the slip velocity :math:`\boldsymbol{u}_{slip}`,

 

The slip velocity between the proppant and carrying fluid includes gravitational and collisional components, which take account of particle settling and collision effects, respectively.

The gravitational component of the slip velocity :math:`\boldsymbol{u}_{slipG}` is written as a form as




where :math:`\boldsymbol{u}_{settling}` is the settling velocity for a single particle, :math:`d_p` is the particle diameter, and :math:`F(c)` is the correction factor to the particle settling velocity in order to account for hindered settling effects as a result of particle-particle interactions,



with the hindered settling coefficient :math:`\lambda_s` as an empirical constant set to 5.9 by default (Barree & Conway, 1995).

The settling velocity for a single particle, :math:`\boldsymbol{u}_{settling}` , is calculated based on the Stokes drag law by default,



Single-particle settling under intermediate Reynolds-number and turbulent flow conditions can also be described respectively by the Allen's equation (Barree & Conway, 1995),



and Newton's equation(Barree & Conway, 1995),




:math:`\boldsymbol{e}` is the unit gravity vector and :math:`d_p` is the particle diameter.

The collisional component of the slip velocity is modeled by defining :math:`\lambda`, the ratio of the particle velocity to the volume averaged mixture velocity as a function of the proppant concentration. From this the particle slip velocity in horizontal direction is related to the mixed fluid velocity by,



with :math:`\boldsymbol{v}_{m}` denoting volume averaged mixture velocity.
We use a simple expression of :math:`\lambda` proposed by Barree & Conway (1995) to correct the particle slip velocity in horizontal direction,



where :math:`\alpha` and :math:`\beta` are empirical constants, :math:`c_{slip}` is the volume fraction exhibiting the greatest particle slip. By default the model parameters are set to the values given in (Barree & Conway, 1995): :math:`\alpha= 1.27`, :math:`c_{slip} =0.1` and :math:`\beta =  1.5`. This model can be extended to account for the transition to the particle pack as the proppant concentration approaches the jamming transition.

### Proppant Bed Build-up and Load Transport
In addition to suspended particle flow the GEOS has the option to model proppant settling into an immobile bed at the bottom of the fracture. As the proppant cannot settle further down the proppant bed starts to form and develop at the element that is either at the bottom of the fracture or has an underlying element already filled with particles. Such an "inter-facial" element is divided into proppant flow and immobile bed regions based on the proppant-pack height.

Although proppant becomes immobile fluid can continue to flow through the settled proppant pack. The pack permeability `K` is defined based on the Kozeny-Carmen relationship:



and



where :math:`\phi` is the porosity of particle pack and :math:`c_{s}` is the saturation or maximum fraction for proppant packing, :math:`s` is the sphericity and :math:`d_p` is the particle diameter.


The growth of the settled pack in an "inter-facial" element is controlled by the interplay between proppant gravitational settling and shear-force induced lifting as (Hu et al., 2018),



where :math:`H`, :math:`t`, :math:`c_{s}`, :math:`Q_{lift}`, and :math:`A` represent the height of the proppant bed, time, saturation or maximum proppant concnetration in the proppant bed, proppant-bed load (wash-out) flux, and cross-sectional area, respectively.

The rate of proppant bed load transport (or wash out) due to shear force is calculated by the correlation proposed by Wiberg and Smith (1989) and McClure (2018),



:math:`a` is fracture aperture, and :math:`N_{sh}` is the Shields number measuring the relative importance of the shear force to the gravitational force on a particle of sediment (Miller et al., 1977; Biot & Medlin, 1985; McClure, 2018) as



and



where :math:`\tau` is the shear stress acting on the top of the proppant bed and :math:`f` is the Darcy friction coefficient. :math:`N_{sh, c}` is the critical Shields number for the onset of bed load transport.


### Proppant Bridging and Screenout
Proppant bridging occurs when proppant particle size is close to or larger than fracture aperture. The aperture at which bridging occurs, :math:`h_{b}`, is defined simply by



in which :math:`\lambda_{b}` is the bridging factor.

### Slurry Fluid Viscosity
The viscosity of the bulk fluid, :math:`\mu_m`, is calculated as a function of proppant concentration as (Keck et al., 1992),




Note that continued model development and improvement are underway and additional empirical correlations or functions will be added to support the above calculations.

