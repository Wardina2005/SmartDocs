-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Jul 28, 2026 at 09:24 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `smartdocs_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `activity_logs`
--

CREATE TABLE `activity_logs` (
  `id` int(11) NOT NULL,
  `user_action` varchar(255) NOT NULL,
  `document_id` int(11) DEFAULT NULL,
  `timestamp` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `activity_logs`
--

INSERT INTO `activity_logs` (`id`, `user_action`, `document_id`, `timestamp`) VALUES
(2, 'Saved OCR document SALFORD', 2, '2026-07-28 01:32:18'),
(3, 'Saved OCR document INV-DEBUG-001', 3, '2026-07-28 01:43:31'),
(4, 'Saved OCR document 123456', 4, '2026-07-28 02:06:00'),
(5, 'Saved OCR document SALFORD', 5, '2026-07-28 02:22:41'),
(6, 'Saved OCR document SALFORD', 6, '2026-07-28 02:39:40'),
(7, 'Saved OCR document 123-456-7890', 7, '2026-07-28 02:54:12'),
(8, 'Saved OCR document 123-456-7890', 8, '2026-07-28 03:30:43'),
(9, 'Saved OCR document -', 9, '2026-07-28 03:38:33'),
(10, 'Saved OCR document SALFORD', 10, '2026-07-28 05:19:05'),
(11, 'Saved OCR document SALFORD', 11, '2026-07-28 05:49:18'),
(12, 'Saved OCR document 123-456-7890', 12, '2026-07-28 07:08:07'),
(13, 'Saved OCR document SALFORD', 13, '2026-07-28 07:15:46');

-- --------------------------------------------------------

--
-- Table structure for table `documents`
--

CREATE TABLE `documents` (
  `id` int(11) NOT NULL,
  `vendor_name` varchar(255) NOT NULL,
  `activity_name` varchar(255) DEFAULT 'Transaksi Umum',
  `invoice_number` varchar(100) DEFAULT NULL,
  `invoice_date` varchar(100) DEFAULT NULL,
  `grand_total` decimal(15,2) NOT NULL DEFAULT 0.00,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `no_invoice` varchar(100) DEFAULT '',
  `division` varchar(100) DEFAULT '',
  `category` varchar(100) DEFAULT '',
  `payment_method` varchar(100) DEFAULT '',
  `description` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `documents`
--

INSERT INTO `documents` (`id`, `vendor_name`, `activity_name`, `invoice_number`, `invoice_date`, `grand_total`, `created_at`, `no_invoice`, `division`, `category`, `payment_method`, `description`) VALUES
(2, 'INVOICE SALFORD & CO.', '', 'SALFORD', '2022-03-27', 750000.00, '2026-07-28 01:32:17', '', '', '', '', ''),
(3, 'Test Vendor', '', 'INV-DEBUG-001', '2026-07-28', 350000.00, '2026-07-28 01:43:31', '', 'Sales', 'Purchase', 'Transfer', 'Debug save with items'),
(4, 'TANGGAL: KEPADA: MAJU BERSAMA DIGITAL', '', '123456', '1999-12-31', 12800000.00, '2026-07-28 02:06:00', '', '', '', '', ''),
(5, 'INVOICE SALFORD & CO.', '', 'SALFORD', '2022-03-27', 750000.00, '2026-07-28 02:22:41', '', '', '', '', ''),
(6, 'INVOICE SALFORD & CO.', '', 'SALFORD', '2022-03-27', 750000.00, '2026-07-28 02:39:39', '', '', '', '', ''),
(7, 'TANGGAL: KEPADA: MAJU BERSAMA DIGITAL', '', '123-456-7890', '1999-12-31', 12800000.00, '2026-07-28 02:54:12', '', '', '', '', ''),
(8, 'TANGGAL: KEPADA: MAJU BERSAMA DIGITAL', '', '123-456-7890', '1999-12-31', 12800000.00, '2026-07-28 03:30:43', '', '', '', '', ''),
(9, 'CV Cahaya MEDIA', '', '-', '2026-07-28', 1500000.00, '2026-07-28 03:38:33', '', '', '', '', ''),
(10, 'INVOICE SALFORD & CO.', '', 'SALFORD', '2022-03-27', 750000.00, '2026-07-28 05:19:05', '', '', '', '', ''),
(11, 'INVOICE SALFORD & CO.', '', 'SALFORD', '2022-03-27', 750000.00, '2026-07-28 05:49:18', '', '', '', '', ''),
(12, 'TANGGAL: KEPADA: MAJU BERSAMA DIGITAL', '', '123-456-7890', '1999-12-31', 6806000.00, '2026-07-28 07:08:07', '', '', '', '', ''),
(13, 'INVOICE SALFORD & CO.', '', 'SALFORD', '2022-03-27', 750000.00, '2026-07-28 07:15:46', '', '', '', '', '');

-- --------------------------------------------------------

--
-- Table structure for table `document_items`
--

CREATE TABLE `document_items` (
  `id` int(11) NOT NULL,
  `document_id` int(11) NOT NULL,
  `item_name` varchar(255) NOT NULL,
  `quantity` int(11) DEFAULT 1,
  `price` decimal(15,2) DEFAULT 0.00,
  `total_price` decimal(15,2) DEFAULT 0.00
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `document_items`
--

INSERT INTO `document_items` (`id`, `document_id`, `item_name`, `quantity`, `price`, `total_price`) VALUES
(2, 2, 'KAOS', 1, 100000.00, 100000.00),
(3, 2, 'JAKET', 1, 200000.00, 200000.00),
(4, 2, 'KAOS POLO', 1, 120000.00, 120000.00),
(5, 2, 'SEPATU', 1, 230000.00, 230000.00),
(6, 2, 'SEPATU', 1, 100000.00, 100000.00),
(7, 3, 'Produk A', 1, 150000.00, 150000.00),
(8, 3, 'Produk B', 2, 100000.00, 200000.00),
(9, 4, 'Paket Desain Logo .00O .0OO', 1, 6000000.00, 6000000.00),
(10, 4, 'Desain Company Profile (12 halaman) .00O0', 1, 5000000.00, 5000000.00),
(11, 4, 'Revisi Mayor', 3, 600000.00, 1800000.00),
(12, 5, 'KAOS', 1, 100000.00, 100000.00),
(13, 5, 'JAKET', 1, 200000.00, 200000.00),
(14, 5, 'KAOS POLO', 1, 120000.00, 120000.00),
(15, 5, 'SEPATU', 1, 230000.00, 230000.00),
(16, 5, 'SEPATU', 1, 100000.00, 100000.00),
(17, 6, 'KAOS', 1, 100000.00, 100000.00),
(18, 6, 'JAKET', 1, 200000.00, 200000.00),
(19, 6, 'KAOS POLO', 1, 120000.00, 120000.00),
(20, 6, 'SEPATU', 1, 230000.00, 230000.00),
(21, 6, 'SEPATU', 1, 100000.00, 100000.00),
(22, 7, 'Paket Desain Logo .00O .0OO', 1, 6000000.00, 6000000.00),
(23, 7, 'Desain Company Profile (12 halaman) .00O0', 1, 5000000.00, 5000000.00),
(24, 7, 'Revisi Mayor', 3, 600000.00, 1800000.00),
(25, 8, 'Paket Desain Logo .00O .0OO', 1, 6000000.00, 6000000.00),
(26, 8, 'Desain Company Profile (12 halaman) .00O0', 1, 5000000.00, 5000000.00),
(27, 8, 'Revisi Mayor', 3, 600000.00, 1800000.00),
(28, 9, 'Bola Voly', 1, 350000.00, 350000.00),
(29, 9, 'Bola Basket', 2, 250000.00, 500000.00),
(30, 9, 'Stik Softball', 1, 250000.00, 250000.00),
(31, 9, '[Bcla Plmpong', 2, 75000.00, 150000.00),
(32, 9, 'Shuttle Cock', 2, 125000.00, 250000.00),
(33, 10, 'KAOS', 1, 100000.00, 100000.00),
(34, 10, 'JAKET', 1, 200000.00, 200000.00),
(35, 10, 'KAOS POLO', 1, 120000.00, 120000.00),
(36, 10, 'SEPATU', 1, 230000.00, 230000.00),
(37, 10, 'SEPATU', 1, 100000.00, 100000.00),
(38, 11, 'KAOS', 1, 100000.00, 100000.00),
(39, 11, 'JAKET', 1, 200000.00, 200000.00),
(40, 11, 'KAOS POLO', 1, 120000.00, 120000.00),
(41, 11, 'SEPATU', 1, 230000.00, 230000.00),
(42, 11, 'SEPATU', 1, 100000.00, 100000.00),
(43, 12, 'Paket Desain Logo .00O .0OO', 1, 6000.00, 6000.00),
(44, 12, 'Desain Company Profile (12 halaman) .00O0', 1, 5000000.00, 5000000.00),
(45, 12, 'Revisi Mayor', 3, 600000.00, 1800000.00),
(46, 13, 'KAOS', 1, 100000.00, 100000.00),
(47, 13, 'JAKET', 1, 200000.00, 200000.00),
(48, 13, 'KAOS POLO', 1, 120000.00, 120000.00),
(49, 13, 'SEPATU', 1, 230000.00, 230000.00),
(50, 13, 'SEPATU', 1, 100000.00, 100000.00);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `activity_logs`
--
ALTER TABLE `activity_logs`
  ADD PRIMARY KEY (`id`),
  ADD KEY `document_id` (`document_id`);

--
-- Indexes for table `documents`
--
ALTER TABLE `documents`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `document_items`
--
ALTER TABLE `document_items`
  ADD PRIMARY KEY (`id`),
  ADD KEY `document_id` (`document_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `activity_logs`
--
ALTER TABLE `activity_logs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;

--
-- AUTO_INCREMENT for table `documents`
--
ALTER TABLE `documents`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;

--
-- AUTO_INCREMENT for table `document_items`
--
ALTER TABLE `document_items`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=51;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `activity_logs`
--
ALTER TABLE `activity_logs`
  ADD CONSTRAINT `activity_logs_ibfk_1` FOREIGN KEY (`document_id`) REFERENCES `documents` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `document_items`
--
ALTER TABLE `document_items`
  ADD CONSTRAINT `document_items_ibfk_1` FOREIGN KEY (`document_id`) REFERENCES `documents` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
