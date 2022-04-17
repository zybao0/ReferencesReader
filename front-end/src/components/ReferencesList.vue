<template>
	<el-container style="height:100%">
		<el-main>
			<el-table :data="tableData"
					  style="width: 100%"
					  :row-class-name="tableRowClassName"
					  height="100%"
					  @selection-change="SelectionChange"
					  row-key="reference_id">
				<el-table-column type="selection" reserve-selection="true" />
				<el-table-column prop="reference_id" label="Index" width="65" />
				<el-table-column prop="reference" label="Reference Name" />
				<el-table-column align="right" width="125">
					<template #header>
						<el-button type="primary" @click="query_bib">查询</el-button>
					</template>
					<template #default="scope">
						<el-button size="small">Edit</el-button>
					</template>
				</el-table-column>
			</el-table>
		</el-main>
		<el-footer>
			<el-row align="middle" style="height: 100%">
				<div class="pagination">
					<el-pagination
								   background
								   @size-change="handleSizeChange"
								   @current-change="handleCurrentChange"
								   :page-sizes="[5,10, 15, 20, 25]"
								   :page-size="pageSize"
								   :current-page.sync="currentPage"
								   layout="total, sizes, prev, pager, next, jumper"
								   :total="totalRow">
					</el-pagination>
				</div>
			</el-row>
		</el-footer>
	</el-container>
</template>

<script>
	export default
		{
			name: 'ReferencesList',
			mounted()
			{
				this.totalRow=this.$store.state.ReferencesList.length
				this.loadItemData();
			},
			methods:
			{
				tableRowClassName({row, rowIndex})
				{
					if (rowIndex === 1)
					{
						return 'warning-row';
					}
					else if (rowIndex === 3)
					{
						return 'success-row';
					}
					return '';
				},
				//页数变换
				handleSizeChange(val)
				{
					this.pageSize = val;
					this.loadItemData();
				},
				//当前页变换
				handleCurrentChange(val)
				{
					this.currentPage = val;
					this.loadItemData();
				},
				// 加载信息
				loadItemData ()
				{
					const start=(this.currentPage-1)*this.pageSize
					const end=this.currentPage*this.pageSize
					this.tableData = this.$store.state.ReferencesList.slice(start,Math.min(end,this.totalRow));
				},
				SelectionChange(row)
				{
					this.selected=[]
					row.forEach((item)=>{this.selected.push(item.reference)})
					console.log(this.selected)
				},
				query_bib()
				{
					console.log(this.selected)
					this.$axios.post('api/querybib',
					{
						querylist: this.selected,
					}).then(function(response)
					{
						console.log(response); //这里 this = undefined
					}).catch((error)=>
					{
						console.log(this); //箭头函数"=>"使this指向vue
					});
				},
	
			},
			data()
			{
				return{ 
					tableData:[],
					currentPage:1,  //当前页
					totalRow:0,//总页数
					pageSize:10,//当前显示条数
					selected:[]
				}
			}
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
</style>