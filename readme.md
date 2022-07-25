## 四川大学微服务自动打卡工具

### 说明:

------

本项目的初衷是解决目前现存微服务打卡的两大问题

1. 需要调用selenium webdriver 因此需要桌面端环境* 不能在无桌面环境的服务器上运行
2. 识别验证码需要依赖外部接口 可能引入付费问题

> * 实际上在纯命令行环境也可以使用chrome-headless等无GUI的浏览器达到纯命令行操作效果，因此第一点其实也不是什么问题


### 本项目特色:

--------

* 未使用selenium模块进行构建，不需要调用浏览器完成数据填报，对于命令行环境更加友好
    * 自带较为完善的日志记录功能
    * 不使用cookie或是api直接进行填报，直接模拟人工手动登陆的方式，更加接近真人操作
* 使用本地验证码识别平台进行识别，不依赖外部提供的api，运行更加稳定
    * 验证码识别平台请参见 [kerlomz/captcha_platform](https://github.com/kerlomz/captcha_platform)
    * 项目中验证码识别网络模型准确率大约在96%左右，在服务器上每张验证码的识别用时大约在0.03s左右，应该比绝大部分打码平台的返回速度要快<br>【谁让我服务器搭在本地了XD
* 使用SQLite数据库，免去配置MYSQL的麻烦，尽力做到开箱即用


### 与其他打卡工具的对比

--------------

| 项目名                                                                        | 登陆实现方式   | 填报实现方式  | 数据来源    | 地址数据来源 | 数据库类型  | 是否支持虚拟定位 |
|----------------------------------------------------------------------------|----------|---------|---------|--------|--------|----------|
| [SCU-ncov-auto-check](https://github.com/randomCui/SCU-ncov-auto-check)    | 本地识别验证码  | 网页url填报 | 上次填报数据  | 上次     | SQLite | 不支持      |
| [SCU-ncov_checkpoint](https://github.com/somenothing/SCU-ncov_checkpoint)  | 外部识别验证码  | 网页url填报 | 上次填报数据  | 上次     | MYSQL  | 支持       |
| [scu-covid-auto-checkin](https://github.com/koinin/scu-covid-auto-checkin) | cookie登陆 | 网页url填报 | 上次填报数据* | 预置地址   | 无      | 不支持      | 
| [ScuDaKa](https://github.com/shanzha09/ScuDaKa)                            | cookie登陆 | 网页url填报 | 预置数据    | 预置地址   | 无      | 不支持      |
| [scu-covid19](https://github.com/HyperMn/scu-covid19)                      | api登陆    | api填报   | 上次填报数据* | 上次*    | 无      | 不支持      |

> 全国可能有不少高校都使用了差不多的打卡模板，导致很多学校的打卡系统实际上可以通用，比如[scu-covid19](https://github.com/HyperMn/scu-covid19)就是从国科大的打卡脚本fork过来的<br>
> 但是**scu-covid19**项目***可能存在问题***，没有验证过其中使用的api是否适用于川带，并且填报的字段与川带目前填报的字段存在较大冲突，建议使用/开发时还是参考其他四个项目<br>
 
### 常见问题

* 为什么这个脚本和[SCU-ncov_checkpoint](https://github.com/somenothing/SCU-ncov_checkpoint)看起来基本上差不多
  * 本来开发对标的就是这个项目，最初是因为我以为selenium不能在命令行界面使用，并且希望不使用外部api识别验证码，不配置MYSQL才开始开发的。直到我在开始写readme的时候才发现chrome也能在无桌面环境的情况下使用，这下算是绕了个大弯了。
* 怎么将服务部署到服务器上呢
  * 之后会更新部署方法，可能还会开发一个代理打卡的功能，什么时候被学校查水表了我就跑路(x) 