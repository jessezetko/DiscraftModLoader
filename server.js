const express = require('express');
const cors = require('cors');
const fileUpload = require('express-fileupload');
const fs = require('fs');
const archiver = require('archiver');

const app = express();
const port = 3000;

// Replace with desired mod upload path
const uploadDir = './uploads';
const zipFilePath = './uploads/modpack.zip';

// Replace with api key
const API_KEY = '?';

function apiKeyCheck(req, res, next) {
    const apiKey = req.get('X-API-Key');
    if (apiKey && apiKey === API_KEY) {
        next();
    } else {
        res.status(401).send('Unauthorized: Invalid API key');
    }
}

app.use(cors());
app.use(fileUpload());

function updateZipFile() {
    const output = fs.createWriteStream(zipFilePath);
    const archive = archiver('zip', {
        zlib: { level: 9 } // Compression level
    });

    output.on('close', function () {
        console.log(archive.pointer() + ' total bytes');
        console.log('Archiver has been finalized and the output file descriptor has closed.');
    });

    archive.on('warning', function (err) {
        if (err.code === 'ENOENT') {
            console.warn(err);
        } else {
            throw err;
        }
    });

    archive.on('error', function (err) {
        throw err;
    });

    archive.pipe(output);

    // Append files from the upload directory
    fs.readdirSync(uploadDir).forEach(file => {
        // Check if the file is a .jar file
        if (file.endsWith('.jar')) {
            archive.append(fs.createReadStream(`${uploadDir}/${file}`), { name: file });
        }
    });

    archive.finalize();
}

app.post('/upload', apiKeyCheck, (req, res) => {
    const modFile = req.files?.modFile ?? null;

    // Check for file
    if (modFile == null) {
        return res.status(400).send("No file provided.");
    }

    // Check file type
    if (!modFile.mimetype.includes('application/java-archive')) {
        return res.status(400).send('Invalid file type. Only JAR files are allowed.');
    }

    // Check if file with the same name already exists
    if (fs.existsSync(`${uploadDir}/${modFile.name}`)) {
        return res.status(400).send('A file with the same name already exists.');
    }

    // Save the file to disk
    modFile.mv(`${uploadDir}/${modFile.name}`, (err) => {
        if (err) {
            return res.status(500).send(err);
        }

        // Update the zip file after each upload
        updateZipFile();

        res.send('File uploaded!');
    });
});

app.listen(port, () => {
    console.log(`Server is listening at http://localhost:${port}`);
});
