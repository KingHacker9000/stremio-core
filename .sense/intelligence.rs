use serde::Serialize;
use std::sync::Arc;
use stremio_sense_recs::{MediaType, SenseIndex};
use crate::models::ctx::Ctx;
use crate::runtime::msg::{Action, ActionIntelligence, Msg};
use crate::runtime::{Effects, Env, UpdateWithCtx};

#[derive(Clone,Debug,Default,PartialEq,Serialize)]
#[serde(tag="type",content="content")]
pub enum IntelligenceStatus{#[default]Unloaded,Ready{items:usize,dimensions:usize},Error(String)}
#[derive(Clone,Debug,PartialEq,Serialize)]
#[serde(rename_all="camelCase")]
pub struct Recommendation{pub id:String,pub name:String,pub r#type:String,pub score:f32}
#[derive(Clone,Debug,Default,Serialize)]
#[serde(rename_all="camelCase")]
pub struct Intelligence{#[serde(skip)]index:Option<Arc<SenseIndex>>,pub status:IntelligenceStatus,pub selected_id:Option<String>,pub recommendations:Vec<Recommendation>}
fn kind(t:MediaType)->&'static str{match t{MediaType::Movie=>"movie",MediaType::Series=>"series",MediaType::Other=>"other"}}
impl<E:Env> UpdateWithCtx<E> for Intelligence{fn update(&mut self,msg:&Msg,_:&Ctx)->Effects{match msg{
Msg::Action(Action::Intelligence(ActionIntelligence::LoadIndex(bytes)))=>{match SenseIndex::from_bytes(bytes){Ok(index)=>{self.status=IntelligenceStatus::Ready{items:index.len(),dimensions:index.dimensions()};self.index=Some(Arc::new(index));self.selected_id=None;self.recommendations.clear()},Err(e)=>{self.status=IntelligenceStatus::Error(e.to_string());self.index=None;self.selected_id=None;self.recommendations.clear()}}Effects::none()}
Msg::Action(Action::Intelligence(ActionIntelligence::Similar{id,candidate_limit,result_limit,relevance_weight}))=>{let Some(index)=self.index.as_ref()else{return Effects::none().unchanged()};let next=index.recommendations(id,*candidate_limit,*result_limit,*relevance_weight).into_iter().map(|h|Recommendation{id:h.id,name:h.name,r#type:kind(h.media_type).into(),score:h.score}).collect::<Vec<_>>();if self.selected_id.as_deref()==Some(id.as_str())&&self.recommendations==next{return Effects::none().unchanged()}self.selected_id=Some(id.clone());self.recommendations=next;Effects::none()}
Msg::Action(Action::Intelligence(ActionIntelligence::Clear))=>{if self.selected_id.is_none()&&self.recommendations.is_empty(){Effects::none().unchanged()}else{self.selected_id=None;self.recommendations.clear();Effects::none()}}
_=>Effects::none().unchanged()}}}
