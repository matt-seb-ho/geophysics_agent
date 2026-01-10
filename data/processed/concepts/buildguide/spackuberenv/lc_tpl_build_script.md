**Context:** Buildguide > SpackUberenv > LC TPL Build Script

## LC TPL Build Script
On LC systems, it is necessary to update the third-party library installations after a change to the configuration. The `setupLC-TPL-uberenv.bash` `script ](https://github.com/GEOS-DEV/thirdPartyLibs/blob/master/scripts/setupLC-TPL-uberenv.bash) is used to build the third-party libraries on multiple LC systems using uberenv:

[`console
    ./setupLC-TPL-uberenv.bash /path/to/shared/installation/directory

This command will also generate a LvArray and GEOS host-config for each specified machine and compiler combination.



