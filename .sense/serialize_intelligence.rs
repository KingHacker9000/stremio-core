#[cfg(feature = "wasm")]
use {gloo_utils::format::JsValueSerdeExt, wasm_bindgen::JsValue};
use stremio_core::models::intelligence::Intelligence;

#[cfg(feature = "wasm")]
pub fn serialize_intelligence(intelligence: &Intelligence) -> JsValue {
    <JsValue as JsValueSerdeExt>::from_serde(intelligence).expect("JsValue from Intelligence")
}
