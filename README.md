## init Env
- scoop install pipx
- pipx install poetry
- poetry env use /mingw64/bin/python
- poetry install
- poetry env info --path (경로확인)
- vscode 인터프리터 추가
## run
- poetry run uvicorn src.human_detect_module:app --reload
## Poetry Local wheel
```
  [tool.poetry.dependencies]
  python = "^3.9"
  opencv-contrib-python = { path = "path/to/opencv_contrib_python-4.x.x-cp39-cp39-linux_x86_64.whl" }
```

# Docker

## 공통
```bash
docker build -f dockerfile.base -t bict/apc-module-base .
docker tag bict/apc-module-base 192.168.0.18:5000/bict/apc-module-base
docker push 192.168.0.18:5000/bict/apc-module-base
```

## 개발용
```bash
docker build -f dockerfile.dev -t bict/apc-module-dev .
docker tag bict/apc-module-dev 192.168.0.18:5000/bict/apc-module-dev
docker push 192.168.0.18:5000/bict/apc-module-dev
docker run -d --gpus all -v %cd%:/app --name apc-module-dev bict/apc-module-dev tail -f /dev/null
```

## 프로덕션용
```bash
docker build -f dockerfile.prod -t bict/apc-module .
docker tag bict/apc-module 192.168.0.185:32000/bict/apc-module
docker push 192.168.0.185:32000/bict/apc-module
docker run --rm --gpus all bict/apc-module
```

## Issue
1.main에서 부팅 타이밍에
  humanDetect API 에 human detect status 받아와서
  run 중으로 DB에 있으면 cctv API에 rtsp 요청
  rtsp 요청에 성공하면 module start

2.module service에 humanDetect API 에 human detect status를 변경하는 로직 추가

3 cctv API, humandetect API httpx instance 추가

