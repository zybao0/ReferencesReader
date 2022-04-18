# ReferencesReader

This project implements a reference parser, which allows users to upload an article to parse out the references in the article and obtain the BIBTex file of the article for users to download.

This project hopes to adapt to as many English academic articles as possible and improve the accuracy of reference extraction as much as possible

## how to build

### front-end

```
$ cd front-end
$ npm install
$ npm run build
```

### back-end

```
$ cd back-end
$ pip install -r requirements.txt
$ mv ../front-end/dist static
```