**Context:** Fileio > Doc > InputXMLFiles > Sublime Text

## Sublime Text
We recommend using the `Exalt ](https://github.com/eerohele/exalt) or [SublimeLinter_xmllint ](https://github.com/SublimeLinter/SublimeLinter-xmllint) plug-ins to validate xml files within sublime.
If you have not done so already, install the sublime [Package Control ](https://packagecontrol.io/installation).
To install the package, press [ctrl + shift + p`, type and select `Package Control: Install Package`, and search for `exalt` or `SublimeLinter` / `SublimeLinter-xmllint`.
Note that, depending on the circumstances, these tools may indicate only a subset of the validation errors at a given time.
Once resolved, the tools should re-check the document to look for any additional errors.

As an additional step for SublimLinter-xmllint, you will need to add a linter configuration.
To do so, go to Preferences/Package Settings/SublimeLinter/Settings.
In the right-hand side of the new window, add the xmllint configuration:

```python
    {
        "linters": {
            "xmllint":
            {
                "args": "--schema /path/to/schema.xsd",
                "styles": [
                    {
                        "mark_style": "fill",
                        "scope": "region.bluish",
                        "types": ["error"],
                        "icon": "stop",
                    }
                ]
            },
        }
    }


