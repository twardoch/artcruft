// this_file: native/mcruft_pdfcraft_native/src/lib.rs
use pdfcraft_cos::{Document, SaveOptions, write_full};
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;
use std::{fs, sync::Arc};

fn error(err: impl std::fmt::Display) -> PyErr {
    PyRuntimeError::new_err(err.to_string())
}

fn read(path: &str) -> PyResult<Document> {
    Document::open(Arc::new(fs::read(path).map_err(error)?)).map_err(error)
}

fn write(doc: &Document, out: &str) -> PyResult<()> {
    let bytes = write_full(doc, &SaveOptions::default()).map_err(error)?;
    fs::write(out, bytes).map_err(error)
}

#[pyfunction]
fn page_count(path: &str) -> PyResult<usize> {
    pdfcraft_organize::page_count(&read(path)?).map_err(error)
}

#[pyfunction]
fn extract(path: &str, pages: Vec<usize>, out: &str) -> PyResult<()> {
    let doc = pdfcraft_organize::extract_pages(&read(path)?, &pages).map_err(error)?;
    write(&doc, out)
}

#[pyfunction]
fn combine(paths: Vec<String>, out: &str) -> PyResult<()> {
    let docs = paths
        .iter()
        .map(|path| read(path))
        .collect::<PyResult<Vec<_>>>()?;
    let sources = paths
        .iter()
        .zip(&docs)
        .map(|(p, d)| (p.as_str(), d))
        .collect::<Vec<_>>();
    write(&pdfcraft_organize::combine(&sources).map_err(error)?, out)
}

#[pymodule]
fn mcruft_pdfcraft_native(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(page_count, module)?)?;
    module.add_function(wrap_pyfunction!(extract, module)?)?;
    module.add_function(wrap_pyfunction!(combine, module)?)?;
    Ok(())
}
