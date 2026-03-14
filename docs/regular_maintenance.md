# Regular Maintenance

## Update year in copyright headings

Every file shoud contain a copyright header with a year range.
The current year can be updated every year with a command line like

```
sed -i 's/-202X/-202Y/g' *.py ./tests/**/*.py ./inyoka/**/*.py LICENSE ./**/*.html ./**/*.less ./**/*.js
```

(replace `X` with the last number of the previouse year and `Y` with the current year.)

`git grep` can help to find missed occurences.
