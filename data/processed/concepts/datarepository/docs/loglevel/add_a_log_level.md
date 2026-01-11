**Context:** Datarepository > LogLevel > Add a log level

## Add a log level
To add a log level, you must respect the following structure and add it to the appropriate `LogLevelsInfos.hpp` :

.. code-block:: c++

    struct MyMessage
    {
        static constexpr int getMinLogLevel() { return 2; }
        static constexpr std::string_view getDescription() { return msg; }
    };

If there is no `LogLevelsInfos.hpp` in the corresponding folder, you can create a `LogLevelsInfos.hpp`.


    while ignoring any polymorphism concern (avoid to add it in a base class, else it can result in undesired documentation entries for other inheriting classes).
    Do not worry to add a logInfo multiple times by on an instance, the system will filter any doubles.
