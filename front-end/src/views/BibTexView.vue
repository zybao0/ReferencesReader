<template>
	<MyTable v-bind="post">
		<el-table-column prop="entryTags.title" label="Title" />
		<el-table-column prop="entryTags.author" label="Author" width="200"/>
	</MyTable>
</template>

<script>
	import MyTable from '@/components/MyTable.vue'
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
					return '';
				},
				SelectionChange(row)
				{
					this.selected=[]
					row.forEach((item)=>{this.selected.push(item.bib)})
				},
				download()
				{
					console.log(this.selected)
					const a = document.createElement('a')
					const blob = new Blob(this.selected,{type:'text/plain'})
					const url = URL.createObjectURL(blob)
					a.setAttribute('href', url)
					a.setAttribute('download', "references.bib")
					a.click()
				},
				getRowKey (row)
				{
					return row.bib
				},
			},
			data()
			{
				return{
					selected:[],
					post:
					{
						TableData:this.$store.state.BibList,
						RowClassName:this.tableRowClassName,
						SelectionChange:this.SelectionChange,
						RowKey:this.getRowKey,
						MainButtonText:"Download",
						MainButtonEvent:this.download,
					},
				}
			},
		}
</script>

