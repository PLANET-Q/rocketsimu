# rocketsimu
ハイブリッドロケット用6自由度弾道シミュレーションライブラリ  
v0.3.0

## Features
- パッケージ化(依存ライブラリは自動インストールされます)
- 6自由度弾道シミュレーション
- べき法則風モデル
- プロセス並列処理
- kml形式落下分散出力

## Dependencies to be installed
- numpy
- numpy-quaternion
- scipy
- pandas
- matplotlib
- numba
- simplekml

## Installation
### Clone
以下のコマンドからgitを使用して作業ディレクトリにクローンするか，
[https://github.com/PLANET-Q/rocketsimu](https://github.com/PLANET-Q/rocketsimu)の 'Clone or Download' ボタンよりZIPファイルをダウンロードして展開します。
```
cd [ダウンロード先フォルダ]
git clone https://github.com/PLANET-Q/rocketsimu
cd rocketsimu
```

### Install
カレントディレクトリを作業ディレクトリに移してから，以下のコマンドでrocketsimuをインストールします。
```
python setup.py install
```

### Uninstall
アンインストールしたい場合は以下のコマンドで削除できます。
```
pip uninstall rocketsimu
```

## Usage

パラメータの設定については[howto_setting_params](https://github.com/PLANET-Q/rocketsimu/blob/master/docs/howto_setting_params.md)を参照してください。

[サンプルフォルダ](https://github.com/PLANET-Q/rocketsimu/blob/master/samples/)を作業ディレクトリにコピーしておきます．
サンプルフォルダ内には単一シミュレーションを行い弾道や速度履歴のグラフを表示する`run_single.py` と，複数条件下のシミュレーションをプロセス並列で行い落下分散を出力する`run_loop.py`が存在します．

### `run_single.py`

ターミナル(orコマンドプロンプト)からサンプルフォルダのディレクトリに移動し，以下のコマンドを実行してシミュレーションを実行します．

```run_single.sh
$ python run_single.py sample_parameters.json -l log.json -s true 
```

- `sample_parameters.json` 引数はシミュレーションパラメータファイルのパスを指定．
- `-l` オプション（任意）はシミュレーション中の中間データを指定したファイル名で出力
- `-s` オプション（任意）に `true` を指定すると弾道などのグラフを表示

オプションの指定方法などを忘れた場合は `python run_single.py -h` を実行すると説明が表示されます．

### `run_loop.py`

サンプルフォルダから以下のコマンドを実行すると落下分散を計算し出力します．

```run_single.sh
$ python run_loop.py sample_parameters.json 8 1:8:1 output/sample -k sample_scatter.kml -p 8
```
- `sample_parameters.json` 部分はシミュレーションパラメータファイルのパスを指定．
- `8` の部分はべき則風モデルにWおける地上基準風向のパターン数．(この場合0, 45, 90, 135, 180, 225, 270, 315degの各風向について計算)
- `1:8:1` 部分はべき則風モデルにおける地上基準風の風速のレンジ．
a:b:c と指定した場合, a[m/s] 以上 b[m/s]未満の範囲の風速を c[m/s] ごとに計算
- `output/sample` 部分は出力先フォルダ名．空のフォルダを指定することが望ましい
- `-k` 引数（任意）が指定された場合，指定したファイル名のkmlファイルとして出力．
- `-p` 引数（任意）が指定された場合，指定された数のプロセス並列を行う．

オプションの指定方法などを忘れた場合は `python run_loop.py -h` を実行すると説明が表示されます．

## Future works/TODO
- 95パーセンタイル統計風モデル
- 予報風対統計風誤差統計モデル
- GUI実装
- 逆問題設計

## Thanks/Acknowledgements
- [shugok](https://github.com/shugok): シミュレーションの本質部分であるソルバ関数へ渡すdu_dt導出関数のアルゴリズムのほぼ全てを提供していただきました。

## LICENSE
このプロジェクトは[MITライセンス](https://github.com/PLANET-Q/rocketsimu/blob/master/LICENSE)のもと公開されています。以下の制限のもと利用可能です。
- このプロジェクト内のソースコードは誰でも自由に利用/改変/再頒布可能ですが，このスクリプトを利用するソースコード内の重要な箇所に著作権表示と[本ライセンス表示](https://github.com/PLANET-Q/TrajecSimu2/blob/master/LICENSE)を付ける必要があります。  
- **このプロジェクト内のソースコードについて作者/著作権者は一切の責任を負いません**