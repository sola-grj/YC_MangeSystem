from django.http.request import QueryDict

# class Pagination:
#     def __init__(self,page,all_count,params = None,per_page=10,max_show=15):
#         try:
#             self.page = int(page)
#             if self.page <= 0:
#                 self.page = 1
#         except Exception:
#             self.page = 1
#             # 总数据数all_count
#         all_count = all_count
#         # 查询条件
#         self.params = params
#         if not self.params:
#             self.params = QueryDict(mutable=True)  # 可编辑的QueryDict
#
#         # 总的页码数total_num
#         total_num, rest = divmod(all_count, per_page)
#         if rest:
#             total_num += 1
#         # 每页要显示的页码数max_show
#         half_show = max_show // 2
#         # 如果总的页码数比每一页显示的页码数还要小，那么给page最小值为1，最大值为总的页码数
#         if total_num <= max_show:
#             page_start = 1
#             page_end = total_num
#         # 或者总的页码数比每一页显示的页码数要大，这时需要分为三种情况来考虑
#         else:
#             # 第一种情况为页码的左侧，即用户选择的页码数比每一页的页码数的一半还小，那么
#             # 就不能继续做page - half_show，这时就需要给page_start赋最小值1
#             if self.page - half_show <= 0:
#                 page_start = 1
#                 page_end = max_show
#             # 第二种情况为页码的右侧，即用户选择的页码数加上每一页页码数的一半还大，那么
#             # 就不能继续做page + half_show，这时需要给page_end赋最大值，即总页码数，page_start
#             # 就可以用总页码数减去每页要显示的页码数+1来实现
#             elif self.page + half_show > total_num:
#                 page_end = total_num
#                 page_start = total_num - max_show + 1
#             # 第三种情况为正常，没有出现在范围之外的情况
#             else:
#                 # 页码的起始值
#                 page_start = self.page - half_show
#                 # 页码的终止值
#                 page_end = self.page + half_show
#         self.page_start = page_start
#         self.page_end = page_end
#         self.total_num = total_num
#         self.start_num = (self.page - 1)*per_page
#         self.end_num = self.page*per_page
#
#     @property
#     def page_html(self):
#         li_list = []
#         # 完成上一页，如果到了第一页，那么对上一页的按钮设置禁用class="disabled"
#         if self.page == 1:
#             li_list.append(
#                 '<li class="disabled"><a href="?page={}" aria-label="Previous"><span aria-hidden="true">&laquo;</span></a></li>'.format(
#                     self.page - 1, ))
#         else:
#             self.params['page'] = self.page-1
#             li_list.append(
#                 '<li><a href="?{}" aria-label="Previous"><span aria-hidden="true">&laquo;</span></a></li>'.format(
#                     self.params.urlencode(), ))
#         # 完成中间的页码显示，并设置客户选择哪一个就设置激活状态class="active"
#         for i in range(self.page_start, self.page_end + 1):
#             self.params['page'] = i
#             if i == self.page:
#                 li_list.append('<li class="active"><a href="?{}">{}</a></li>'.format(self.params.urlencode(), i))
#             else:
#                 li_list.append('<li><a href="?{}">{}</a></li>'.format(self.params.urlencode(), i))
#         # 完成下一页，如果到了最后一页，那么对下一页的按钮设置禁用class="disabled"
#         if self.page == self.total_num:
#             li_list.append(
#                 '<li class="disabled"><a href="?page={}" aria-label="Next"><span aria-hidden="true">&raquo;</span></a></li>'.format(
#                     self.page + 1, ))
#         else:
#             li_list.append(
#                 '<li><a href="?page={}" aria-label="Next"><span aria-hidden="true">&raquo;</span></a></li>'.format(
#                     self.page + 1, ))
#         return ''.join(li_list)
from django.http.request import QueryDict
from django.utils.safestring import mark_safe


class Pagination:
    """
    page: 当前的页码数
    all_count： 总的数据量
    per_num ：  每页显示的数据量
    max_show：  最多显示的页码数
    """

    def __init__(self, page, all_count, params=None, per_num=10, max_show=11):
        try:
            self.page = int(page)
            if self.page <= 0:
                self.page = 1
        except Exception:
            self.page = 1
        # 查询条件
        self.params = params
        if not self.params:
            self.params = QueryDict(mutable=True)
        # 总的数据量
        all_count = all_count
        # 每页显示的数据量  10

        # 总的页码数
        total_num, more = divmod(all_count, per_num)
        if more:
            total_num += 1
        # 最大显示的页码数
        half_show = max_show // 2

        if total_num <= max_show:
            page_start = 1
            page_end = total_num
        else:
            if self.page - half_show <= 0:
                # 页码的起始值
                page_start = 1
                # 页码的终止值
                page_end = max_show
            elif self.page + half_show > total_num:
                page_end = total_num
                page_start = total_num - max_show + 1

            else:
                # 页码的起始值
                page_start = self.page - half_show
                # 页码的终止值
                page_end = self.page + half_show

        self.page_start = page_start
        self.page_end = page_end
        self.total_num = total_num
        self.start_num = (self.page - 1) * per_num
        self.end_num = self.page * per_num

    @property
    def page_html(self):
        li_list = []

        if self.page == 1:
            li_list.append(
                '<li class="disabled"><a aria-label="Previous"> <span aria-hidden="true">&laquo;</span></a></li>')
        else:
            self.params['page'] = self.page -1   # { query:13 ,page : 1 }
            li_list.append(
                '<li><a href="?{}" aria-label="Previous"> <span aria-hidden="true">&laquo;</span></a></li>'.format(
                    self.params.urlencode()))   #  ?query=13&page=1

        for i in range(self.page_start, self.page_end + 1):
            self.params['page'] = i  # { query:13 ,page : i}
            if i == self.page:
                li_list.append('<li class="active"><a href="?{}">{}</a></li>'.format(self.params.urlencode(), i))
            else:
                li_list.append('<li><a href="?{}">{}</a></li>'.format(self.params.urlencode(), i))

        if self.page == self.total_num:
            li_list.append(
                '<li class="disabled"><a aria-label="Next"> <span aria-hidden="true">&raquo;</span></a></li>')
        else:
            self.params['page'] = self.page + 1
            li_list.append(
                '<li><a href="?{}" aria-label="Next"> <span aria-hidden="true">&raquo;</span></a></li>'.format(
                    self.params.urlencode()))

        return mark_safe(''.join(li_list))
