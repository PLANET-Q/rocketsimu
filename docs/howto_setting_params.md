# パラメータJSONファイルのセッティング
For version 0.1.0
# パラメータのサンプル
[sample.json](https://github.com/PLANET-Q/rocketsimu/blob/master/samples/sample_parameters.json)を参照

# 解説

|項目名|内容|
|---|---|
|height|ロケット全長[m]|
|diameter|ロケットボディの直径[m]|
|mass_dry|乾燥時重量[kg]|
|CG_dry|乾燥時重心位置[m]. ノーズ先端からの距離とする|
|MOI_dry|乾燥時慣性モーメント[kg m^2]. ロール,ピッチ,ヨーのリストで指定する必要があります|
|Cm|モーメント係数(安定微係数). ロール,ピッチ,ヨーの順のリスト|
|lug_1st|最もノーズに近いランチラグのノーズ先端からの位置[m]|
|lug_2nd|2番目にノーズに近いランチラグのノーズ先端からの位置[m]|
|Cd0|マッハ0.1, 仰角0degreeでの抗力係数値|
|Clalpha|揚力傾斜値|
|CP|空力中心位置. ノーズ先端からの長さとする.|
|MOI_prop|推進剤慣性モーメント[kg m^2]. ロール,ピッチ,ヨーのリスト|
|mass_prop|離床前の推進剤の重量[kg].|
|CG_prop|ノーズ先端から推進剤重心位置までの距離[m].|
|thrust_curve_csv|スラストカーブのcsvファイル名. 詳細は次節|
|thrust_dt|スラストカーブのサンプリング間隔[s]|
|latitude|ランチャ地点の緯度[deg]. 現在未使用|
|longitude|ランチャ地点の経度[deg]. 現在未使用|
|alt_launcher|ランチャ地点の標高[m]. 現在未使用|
|azimuth|ランチャ方位角[deg]|
|elev_angle|ランチャ仰角[deg]|
|rail_length|ランチャレール長[m]|
|t_max|シミュレーションする最長時間[s].|
|is_drogue|ドローグシュートを使用するかどうか. `true` または`false` が指定可能|
|Cd_drogue|ドローグシュートの抗力係数. `is_drogue` が `false` の場合無視される|
|S_drogue|ドローグシュートの有効面積. `is_drogue` が `false` の場合無視される|
|Cd_para|メインパラシュートの抗力係数|
|S_para|メインパラシュートの有効面積|
|drogue_trigger|ドローグシュート展開条件. ディクショナリ`{}` で指定する.詳細は後述|
|para_trigger|メインパラシュート展開条件. ディクショナリ`{}` で指定する.詳細は後述|
|wind_model|風モデルの種類. 現在'constant', 'power', 'forecast', 'hybrid'が指定可能|
|wind_parameters|風モデルに応じたパラメータのディクショナリ. 詳細は後述|
# スラストカーブ
スラストカーブのcsvファイルは、以下のような形式とし、
`$`, `#`, `%`を行頭につけることでコメント行とみなせる.

```
#t[s], Thrust[N]
0.0000, 0.000
0.0001, 0.003
....
6.0000, 0.000
```
# パラシュート展開条件の指定方法
ドローグ/メインパラシュート展開条件は, それぞれ`drogue_trigger:{}`, `para_trigger:{}`の`{}`内で設定できる.
設定できる展開条件は以下の三種類である. 複数の条件を設定する場合はカンマ`,`で区切って条件を追加する.この場合, いずれかの条件が1つでも満たされた時にパラシュート展開する. 

|展開条件の名前|内容|
----|----
|"flight_time"|離床からの経過時間[s]|
|"fall_time"|頂点時刻からの経過時間[s]|
|"altitude"|ランチャ位置に対する高度(落下時)[m]|

したがって,以下のように設定すると,ドローグシュートは頂点時刻から1秒後に展開,
メインパラシュートは離床から1800秒後,または落下時に高度300mを過ぎた場合に展開となる.
```

"drogue_trigger": {
        "fall_time": 1.0
    },

"para_trigger": {
    "flight_time": 1800,
    "altitude": 300
},

```
# 風モデルの指定方法
風モデルの指定は, `wind_model`と`wind_parameters`から行える.  
`wind_model`には風モデルの名称を指定する.現在対応しているのは以下の3種類の風モデルとハイブリッドモデルである.
- `constant`: 定常風モデル
- `power`: べき法則モデル
- `forecast`: 予報風モデル
- `hybrid`: ハイブリッドモデル

`wind_parameters`には指定した風モデルに必要なパラメータをディクショナリ(`{}`の中にデータを指定する形式)形式で指定する.  
各モデルに対して指定すべきパラメータは以下の通りである.

|風モデル|指定パラメータ|説明|
----|----|----
|constant|wind_std| 定常風の風ベクトルをx,y,zの順のリストで指定する|
|power|z0|基準高度
||n|べき法則の係数
||wind_std| 基準高度における基準風ベクトル. x,y,zの順のリスト
|forecast|filename|予報風ファイルのファイル名.|
|hybrid|wind0|1つ目の風モデルをディクショナリで指定する.詳細は以下
||wind1|2つ目の風モデルをディクショナリで指定する.詳細は以下
||kind| 風モデルの補完メソッドを文字列指定する. 現在は'linear'のみ対応
||border_height0|wind0→wind1に遷移し始める境界となる高度.
||border_height1|wind0→wind1への遷移が終了する高度.
||weight0|遷移前のwind0/wind1の比率
||weight1|遷移後のwind0/wind1の比率

`wind0`, `wind1`パラメータに指定する風モデルは、その風モデルをこの節にしたがってディクショナリ化したものを指定すれば良い.  
以下に例を示す.
```
"wind_model":"hybrid",
"wind_parameters":{
    "wind0":{
        "wind_model":"power",
        "wind_parameters":{
            "z0": 2.0,
            "n": 4.5,
            "wind_std": [5.0, 0.0, 0.0]
        }
    },
    "wind1":{
        "wind_model":"forecast",
        "wind_parameters":{
            "filename":"forecast_wind.csv"
        }
    },
    ...(以下略)
}
```