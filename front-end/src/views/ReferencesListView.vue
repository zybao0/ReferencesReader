<template>
	<MyTable v-bind="post" :MainButtonLoading="isLoading">
		<el-table-column prop="reference" label="Reference Name" />
	</MyTable>
	<el-dialog v-model="DialogFormVisible" title="Edit" >
		<el-input
			v-model="NowContent"
			autosize
			type="textarea"
			placeholder="Please input"
		/>
		<el-switch
			v-model="addNewRow"
			size="large"
			active-text="Add a new row"
		/>
		<el-input
			v-model="NewRowContent"
			autosize
			type="textarea"
			placeholder="Please input"
			v-show="addNewRow"
		/>
		<template #footer>
			<el-button type="primary" @click="HandleDialogConfirm">Confirm</el-button>
		</template>
	</el-dialog>
</template>

<script>
	import MyTable from '@/components/MyTable.vue'
	import { h } from 'vue'
	import { ElMessage, ElMessageBox } from 'element-plus'
	export default
		{
			name: 'ReferencesListView',
			components:
			{
				MyTable
			},
			methods:
			{
				tableRowClassName({row, rowIndex})
				{
					if(this.$store.state.QueriedReferences[row.reference])return 'success-row';
					return '';
				},
				SelectionChange(row)
				{
					this.selected=[]
					row.forEach((item)=>{this.selected.push(item.reference)})
				},
				query_bib()
				{
					if(this.selected.length==0)
					{
						this.$alert('Please select more than one reference', 'Fail',
						{
							confirmButtonText: 'confirm',
						})
						return
					}
					this.isLoading=true
					this.$axios.post('api/querybib',
					{
						querylist: this.selected,
					}).then((response)=>
					{
						response.data.forEach((item,index)=>
						{
							this.$store.commit("addQueriedReferences",item["RawReference"])
							this.$store.commit("addBIB",item["Bib"])
						})
						this.isLoading=false
					}).catch((error)=>
					{
						console.log(error); //箭头函数"=>"使this指向vue
						this.isLoading=false
					});
				},
				getRowKey(row)
				{
					return row.reference
				},
				Selectable(row)
				{
					if(this.$store.state.QueriedReferences[row.reference] || this.isLoading)return false
					else return true
				},
				HandleRowClick(row)
				{
					this.OldContent=row.reference
					this.NowContent=row.reference
					this.NewRowContent=""
					this.addNewRow=false
					this.DialogFormVisible=true
				},
				HandleDialogConfirm()
				{
					this.$store.commit('editReference',
					{
						OldReference:this.OldContent,
						NewRow:this.addNewRow,
						NewReference:this.NowContent,
						NewRowReference:this.NewRowContent
					})
					this.DialogFormVisible=false
					console.log(this.$store.state.ReferencesList)
				},
			},
			data()
			{
				return{
					selected:[],
					isLoading:false,
					DialogFormVisible:false,
					OldContent:"",
					NowContent:"",
					NewRowContent:"",
					addNewRow:false,
					post:
					{
						TableData:this.$store.state.ReferencesList,
						RowClassName:this.tableRowClassName,
						SelectionChange:this.SelectionChange,
						RowKey:this.getRowKey,
						Selectable:this.Selectable,
						ClSelection:this.$store.state.QueriedReferences,
						MainButtonText:"Get BIB!",
						MainButtonEvent:this.query_bib,
						HandleRowClick:this.HandleRowClick,
					},
				}
			},
		}
</script>


<style>
	.el-table .warning-row
	{
		--el-table-tr-bg-color: var(--el-color-warning-light-9);
	}
	.el-table .success-row
	{
		--el-table-tr-bg-color: var(--el-color-success-light-9);
	}

	.el-textarea__inner
	{
        resize: none !important;
    }
	.el-dialog__body
	{
		padding-top:5 !important;
		padding-bottom:0 !important;
	}
</style>