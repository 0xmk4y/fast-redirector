python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
echo "*" > .venv/.gitignore
pip install "fastapi[standard]"
pip install supabase

docker build -t fast-redirctor .
docker run -d -p 80:80 fast-redirctor