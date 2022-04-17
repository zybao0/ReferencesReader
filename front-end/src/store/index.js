import
{
	createStore
}
from 'vuex'

export
default createStore(
{
	state:
	{
		ReferencesList:[],
		BibList:[],
		QueriedReferences:{},
	},
	getters:{},
	mutations:
	{
		setReferencesList(state,payload)
		{
			state.ReferencesList=[]
			payload.forEach((item,index)=>
			{
				state.ReferencesList[index]=
				{
					"reference":item,
				}
			})
		},
		editReference(state,payload)
		{
			let result=state.ReferencesList.findIndex(item=>
			{
				return item.reference==payload.OldReference
			});
			if(result==-1)return
			if(payload.NewRow==false)state.ReferencesList.splice(result,1,{"reference":payload.NewReference})
			else state.ReferencesList.splice(result,1,{"reference":payload.NewReference},{"reference":payload.NewRowReference})

		},
		addBIB(state,payload)
		{
			let bib=payload.concat("\n")
			let result=state.BibList.findIndex(item=>
			{
				return item.bib==bib
			});
			if(result!=-1)return
			let bibtexParse=require('@orcid/bibtex-parse-js');
			let bibinfo=bibtexParse.toJSON(payload);
			bibinfo[0]["bib"]=bib
			state.BibList.push(bibinfo[0])
		},
		addQueriedReferences(state,payload)
		{
			state.QueriedReferences[payload]=true
		},
		deleteList(state,payload)
		{
			payload.item.splice(payload.index,1)
		},
	},
	actions: {},
	modules: {}
})