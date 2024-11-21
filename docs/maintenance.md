# Maintenance

## How to launch OCR on previously uploaded images

OCR (through Google Cloud Vision) is launched on every new proof image. However, if you want to launch OCR on previously uploaded images, you can do so by running the following command:

```bash
make cli args='run_ocr'
```

To override existing OCR results, add the `--override` flag:

```bash
make cli args='run_ocr --override'
```
