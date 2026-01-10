**Context:** Datarepository > LogLevel > Example of usage

## Example of usage
To log a message with a log level, 4 macros are defined in LogLevelsInfo.hpp located in dataRepository:

* `GEOS_LOG_LEVEL( logInfoStruct, msg )`: Output messages based on current `Group`'s log level.
* `GEOS_LOG_LEVEL_RANK_0( logInfoStruct, msg )`: Output messages (only on rank 0) based on current `Group`'s log level.
* `GEOS_LOG_LEVEL_BY_RANK( logInfoStruct, msg )`: Output messages (with one line per rank) based on current `Group`'s log level.
* `GEOS_LOG_LEVEL_RANK_0_NLR( logInfoStruct, msg )`: Output messages (only on rank 0) based on current `Group`'s log level without the line return.

If you want to add a log level with a target log level belonging to another group, 
4 others macro with the same mecanism are defined in LogLevelsInfo.hpp located in dataRepository:

* `GEOS_LOG_LEVEL_ON_GROUP( logInfoStruct, msg, group )`: Output messages based on targeted `group`'s log level.
* `GEOS_LOG_LEVEL_RANK_0_ON_GROUP( logInfoStruct, msg, group )`: Output messages (only on rank 0) based on targeted `group`'s log level.
* `GEOS_LOG_LEVEL_BY_RANK_ON_GROUP( logInfoStruct, msg, group )`: Output messages (with one line per rank) based on targeted `group`'s log level.
* `GEOS_LOG_LEVEL_RANK_0_NLR_ON_GROUP( logInfoStruct, msg, group )`: Output messages (only on rank 0) based on targeted `group`'s log level without the line return.

An exemple of adding and using a log level in a `group`:

.. code-block:: c++

    MyGroup::MyGroup( string const & name );
    {
        // To use a log level, make sure it is declared in the constructor of the group
        addLogLevel< logInfo::MyMessage >();
    }

    void MyGroup::outputMessage()
    {
        // effectively output the message taking into account the log level of the group instance
        GEOS_LOG_LEVEL( logInfo::MyMessage, "output some message" );
    }
