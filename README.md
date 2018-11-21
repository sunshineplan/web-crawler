# web-crawler
collect data from web(JD.com, dangdang.com, amazon.cn, taobao.com, etc.)

### 相对于[原版程序](https://github.com/LewisTian/RAM-JD)，该版本主要改动如下：
- 1.设计成在命令行环境下运行，后面的第一个参数为搜索关键字，第二个参数为保存路径。如`jingdong.py 笔记本内存条 d:\`
- 2.自动获取页码数，并按照该页码数抓取数据（各网站最多也只有100页），如无结果也会提示
- 3.由输出到数据库改为输出成CSV文件（为了方便，不用搭数据库环境，可用Excel软件直接打开）
- 4.使用内置库替换requests库，运行环境除了Python之外只需安装BeautifulSoup4即可
- 5.增加抓取当当网、亚马逊图书的内容
- 6.增加了主控制程序，一个命令即可调用不同的网站库
- 7.增加多线程

### 次要改动：
- 1.去除一些不影响运行的headers，并简化了抓取地址
- 2.更改了京东的产品排序（因工作需要）
- 3.调整一些字段（因工作需要）
