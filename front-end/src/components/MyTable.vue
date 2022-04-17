<template>
	<el-container style="height:100%">
		<el-main>
			<el-table :data="CurrentTableData"
					  style="width:100%"
					  :row-class-name="RowClassName"
					  height="100%"
					  @selection-change="SelectionChange"
					  @row-dblclick="HandleRowClick"
					  :row-key="RowKey"
					  ref="multipleTable">
				<el-table-column type="selection" :reserve-selection="true" :selectable="Selectable"/>
				<el-table-column type="index" :index="IndexMethod" label="Index" width="65"/>
				<slot></slot>
				<el-table-column align="right" width="175">
					<template #header>
						<el-button type="primary" @click="MainButtonEvent" :loading="MainButtonLoading">{{MainButtonText}}</el-button>
					</template>
					<template #default="scope">
						<el-button size="small" type="danger" @click="del(scope.row, scope.$index)">Delete</el-button>
					</template>
				</el-table-column>
			</el-table>
		</el-main>
		<el-footer>
			<el-row align="middle" style="height:100%">
				<div class="pagination">
					<el-pagination background
								  @size-change="handleSizeChange"
								  @current-change="handleCurrentChange"
								  :page-sizes="[5,10, 15, 20, 25]"
								  :page-size="PageSize"
								  :current-page.sync="CurrentPage"
								   layout="total,sizes,prev,pager,next,jumper"
								  :total="TotalRow">
					</el-pagination>
				</div>
			</el-row>
		</el-footer>
	</el-container>
</template>

<script>
	export default
		{
			name: 'MyTable',
			methods:
			{
				//页数变换
				handleSizeChange(val)
				{
					this.PageSize=val
				},
				//当前页变换
				handleCurrentChange(val)
				{
					this.CurrentPage=val
				},
				// 加载信息
				IndexMethod(index)
				{
					return (this.CurrentPage-1)*this.PageSize+index;
				},
				del(row,index)
				{
					this.$store.commit('deleteList',
					{
						item:this.TableData,
						index:index,
					})
					// console.log(this.TableData)
				},
			},
			data()
			{
				return{
					CurrentPage:1,  //当前页
					PageSize:10,//当前显示条数
				}
			},
			props:
			{
				TableData:Array,
				RowClassName:Function,
				SelectionChange:Function,
				RowKey:Function,
				Selectable:
				{
					type:Function,
					default:(row)=>{return true},
				},
				ClSelection:
				{
					type:[String,Number,Boolean,Array,Object,],
					default:false,
				},
				MainButtonText:String,
				MainButtonEvent:Function,
				MainButtonLoading:
				{
					type:Boolean,
					default:false,
				},
				HandleRowClick:
				{
					type:Function,
					default:(row,column,event)=>{},
				},
			},
			watch:
			{
				ClSelection:
				{
					handler()
					{
						this.$refs.multipleTable.clearSelection()
					},
					deep:true
				}

			},
			computed:
			{
				CurrentTableData()
				{
					const start=(this.CurrentPage-1)*this.PageSize
					const end=this.CurrentPage*this.PageSize
					return this.TableData.slice(start,Math.min(end,this.TotalRow))
				},
				TotalRow()
				{
					return this.TableData.length
				}
			}
		}
</script>
