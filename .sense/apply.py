#!/usr/bin/env python3
from pathlib import Path
import shutil,sys
HERE=Path(__file__).resolve().parent
core=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
def repl(s,a,b,label):
    if b in s:return s
    if a not in s:raise SystemExit(f'upstream anchor changed: {label}')
    return s.replace(a,b,1)
def patch(path,fn):
    s=path.read_text();n=fn(s)
    if n!=s:path.write_text(n);print('patched',path)
if not (core/'stremio-core-web').exists():raise SystemExit('not stremio-core')
dst=core/'stremio-sense-recs'
if dst.exists():shutil.rmtree(dst)
shutil.copytree(HERE/'recs-core',dst)
shutil.copy2(HERE/'intelligence.rs',core/'src/models/intelligence.rs')
shutil.copy2(HERE/'serialize_intelligence.rs',core/'stremio-core-web/src/model/serialize_intelligence.rs')
patch(core/'Cargo.toml',lambda s:repl(repl(s,'members = ["stremio-core-web", "stremio-derive", "stremio-watched-bitfield"]','members = ["stremio-core-web", "stremio-derive", "stremio-watched-bitfield", "stremio-sense-recs"]','workspace'),'stremio-watched-bitfield = { path = "stremio-watched-bitfield" }','stremio-watched-bitfield = { path = "stremio-watched-bitfield" }\nstremio-sense-recs = { path = "stremio-sense-recs" }','dependency'))
patch(core/'src/models/mod.rs',lambda s:repl(s,'pub mod installed_addons_with_filters;\n','pub mod installed_addons_with_filters;\npub mod intelligence;\n','model module'))
def actions(s):
    block='''#[derive(Clone, Deserialize, Debug)]\n#[serde(tag = "action", content = "args")]\npub enum ActionIntelligence {\n    LoadIndex(Vec<u8>),\n    #[serde(rename_all = "camelCase")]\n    Similar { id: String, candidate_limit: usize, result_limit: usize, relevance_weight: f32 },\n    Clear,\n}\n\n'''
    if 'pub enum ActionIntelligence' not in s:s=repl(s,'#[derive(Clone, Deserialize, Debug)]\n#[serde(tag = "action", content = "args")]\npub enum ActionSearch {',block+'#[derive(Clone, Deserialize, Debug)]\n#[serde(tag = "action", content = "args")]\npub enum ActionSearch {','ActionSearch')
    return repl(s,'    MetaDetails(ActionMetaDetails),\n    StreamingServer(ActionStreamingServer),','    MetaDetails(ActionMetaDetails),\n    Intelligence(ActionIntelligence),\n    StreamingServer(ActionStreamingServer),','Action Intelligence')
patch(core/'src/runtime/msg/action.rs',actions)
def model(s):
    s=repl(s,'        installed_addons_with_filters::InstalledAddonsWithFilters,\n','        installed_addons_with_filters::InstalledAddonsWithFilters,\n        intelligence::Intelligence,\n','model import')
    s=repl(s,'    pub local_search: LocalSearch,\n    pub meta_details: MetaDetails,','    pub local_search: LocalSearch,\n    pub intelligence: Intelligence,\n    pub meta_details: MetaDetails,','model field')
    s=repl(s,'            local_search,\n            continue_watching_preview,','            local_search,\n            intelligence: Intelligence::default(),\n            continue_watching_preview,','model init')
    return repl(s,'            WebModelField::LocalSearch => serialize_local_search(&self.local_search),\n            WebModelField::MetaDetails =>','            WebModelField::LocalSearch => serialize_local_search(&self.local_search),\n            WebModelField::Intelligence => serialize_intelligence(&self.intelligence),\n            WebModelField::MetaDetails =>','model state')
patch(core/'stremio-core-web/src/model/model.rs',model)
patch(core/'stremio-core-web/src/model/mod.rs',lambda s:repl(s,'mod serialize_installed_addons;\nuse serialize_installed_addons::*;\n','mod serialize_installed_addons;\nuse serialize_installed_addons::*;\n\nmod serialize_intelligence;\nuse serialize_intelligence::*;\n','serializer mod'))
patch(core/'stremio-core-web/src/lib.rs',lambda s:repl(s,'        serialize_discover::serialize_discover,\n        serialize_installed_addons::serialize_installed_addons,','        serialize_discover::serialize_discover,\n        serialize_installed_addons::serialize_installed_addons,\n        serialize_intelligence::serialize_intelligence,','serializer export'))
def wasm(s):
    s=repl(s,'    runtime::{msg::Action, Env, EnvError, Runtime, RuntimeAction, RuntimeEvent},','    runtime::{msg::{Action, ActionIntelligence}, Env, EnvError, Runtime, RuntimeAction, RuntimeEvent},','wasm import')
    fn='''\n#[wasm_bindgen]\npub fn load_sense_index(bytes: &[u8]) -> Result<(), JsValue> {\n    let runtime_action: RuntimeAction<WebEnv, WebModel> = RuntimeAction { action: Action::Intelligence(ActionIntelligence::LoadIndex(bytes.to_vec())), field: Some(WebModelField::Intelligence) };\n    dispatch_internal(runtime_action, None).map_err(|state_err| { error!(?state_err, "Failed to load Sense index due to"); JsValue::from(DispatchError::State(state_err)) })\n}\n\n'''
    if 'pub fn load_sense_index' not in s:s=repl(s,'#[wasm_bindgen]\npub fn dispatch(action: JsValue, field: JsValue, location_hash: JsValue) -> Result<(), JsValue> {',fn+'#[wasm_bindgen]\npub fn dispatch(action: JsValue, field: JsValue, location_hash: JsValue) -> Result<(), JsValue> {','wasm dispatch')
    return s
patch(core/'stremio-core-web/src/stremio_core_web.rs',wasm)
print('Sense Intelligence installed')
