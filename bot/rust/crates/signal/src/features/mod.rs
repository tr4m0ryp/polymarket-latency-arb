//! The decision row (raw.py `row`), the pzm fair value, the model input vectors and the gate's
//! book-survival extras.
pub mod extras;
pub mod fair;
pub mod names;
pub mod row;
pub mod vector;

pub use extras::{extras, EXTRA};
pub use fair::Pzm;
pub use names::Row;
pub use row::row;
pub use vector::Vectorizer;
