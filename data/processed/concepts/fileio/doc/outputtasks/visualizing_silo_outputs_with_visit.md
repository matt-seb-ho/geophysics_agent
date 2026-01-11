**Context:** Fileio > Doc > OutputTasks > Visualizing Silo outputs with VisIT

# Visualizing Silo outputs with VisIT
If the `<Silo>` XML node was defined, GEOS writes the results in a folder called `siloFiles`.

In VisIT :

1. File > Open file...
2. On the right panel, browse to the `siloFiles` folder.
3. On the left panel, select the file(s) you want to visualize. Usually, one file is written according the
   frequency defined in the `timeFrequency` keyword of the Event that has triggered the output.
4. To load fields, use the "Add" button and browse to the fields you want to plot.
5. To plot fields, use the "Draw" button.

Please consult the VisIT_ documentation for further explanations on its usage.

